#!/usr/bin/env python3
"""
User Configuration Database
Manages user setup, email confirmation, and minting addresses
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserConfigDB:
    """Database manager for user configuration and setup"""

    def __init__(self, db_path: str = "db/user_config.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database with user config schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.executescript('''
            -- User configuration
            CREATE TABLE IF NOT EXISTS user_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                email_confirmed BOOLEAN DEFAULT FALSE,
                confirmation_token TEXT,
                confirmation_sent_at TIMESTAMP,
                confirmed_at TIMESTAMP,
                setup_completed BOOLEAN DEFAULT FALSE,
                setup_completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                marketing_opt_in BOOLEAN DEFAULT TRUE
            );

            -- Artist profiles (one artist can have multiple addresses)
            CREATE TABLE IF NOT EXISTS artist_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES user_config(id) ON DELETE CASCADE,
                artist_name TEXT NOT NULL,
                folder_name TEXT UNIQUE NOT NULL,
                bio TEXT,
                is_current BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                license_type TEXT DEFAULT 'free',  -- 'free', 'enterprise', 'white_label'
                max_addresses INTEGER DEFAULT 3,   -- Free: 3, Enterprise: 3 per artist
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Minting addresses (each gets own folder, linked to artist)
            CREATE TABLE IF NOT EXISTS minting_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES user_config(id) ON DELETE CASCADE,
                artist_profile_id INTEGER REFERENCES artist_profiles(id) ON DELETE CASCADE,
                address TEXT NOT NULL,
                address_folder TEXT UNIQUE NOT NULL,  -- Folder name for this specific wallet
                network TEXT DEFAULT 'ethereum',
                label TEXT,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, address)
            );

            -- License tracking for enterprise/white label
            CREATE TABLE IF NOT EXISTS license_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES user_config(id) ON DELETE CASCADE,
                license_type TEXT NOT NULL,  -- 'free', 'enterprise', 'white_label'
                max_artists INTEGER DEFAULT 1,  -- Free: 1, Enterprise: 5, White Label: custom
                customer_service BOOLEAN DEFAULT FALSE,
                white_label_custom BOOLEAN DEFAULT FALSE,
                monthly_updates BOOLEAN DEFAULT FALSE,
                license_key TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Setup progress tracking
            CREATE TABLE IF NOT EXISTS setup_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES user_config(id) ON DELETE CASCADE,
                step_name TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_user_email ON user_config(email);
            CREATE INDEX IF NOT EXISTS idx_confirmation_token ON user_config(confirmation_token);
            CREATE INDEX IF NOT EXISTS idx_minting_user ON minting_addresses(user_id);
            CREATE INDEX IF NOT EXISTS idx_artist_folder ON artist_profiles(folder_name);
            CREATE INDEX IF NOT EXISTS idx_artist_current ON artist_profiles(is_current);
        ''')

        conn.commit()
        conn.close()

        logger.info(f"User configuration database initialized at {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def is_setup_complete(self) -> bool:
        """Check if initial setup has been completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT setup_completed FROM user_config WHERE setup_completed = 1 LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return bool(result)

    def create_user(self, email: str, marketing_opt_in: bool = True) -> int:
        """Create new user with email"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Generate confirmation token
        confirmation_token = secrets.token_urlsafe(32)

        cursor.execute('''
            INSERT INTO user_config (email, confirmation_token, confirmation_sent_at, marketing_opt_in)
            VALUES (?, ?, ?, ?)
        ''', (email.lower(), confirmation_token, datetime.now(), marketing_opt_in))

        user_id = cursor.lastrowid

        # Initialize setup steps
        steps = ['email_confirmation', 'minting_addresses', 'configuration_complete']
        for step in steps:
            cursor.execute('''
                INSERT INTO setup_steps (user_id, step_name, completed)
                VALUES (?, ?, ?)
            ''', (user_id, step, False))

        conn.commit()
        conn.close()

        logger.info(f"Created user: {email} (ID: {user_id})")
        return user_id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_config WHERE email = ?', (email.lower(),))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """Get user by confirmation token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_config WHERE confirmation_token = ?', (token,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def confirm_email(self, token: str) -> bool:
        """Confirm user email with token"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE user_config
            SET email_confirmed = 1, confirmed_at = ?
            WHERE confirmation_token = ? AND email_confirmed = 0
        ''', (datetime.now(), token))

        rows_affected = cursor.rowcount

        if rows_affected > 0:
            # Mark email confirmation step as complete
            cursor.execute('''
                UPDATE setup_steps
                SET completed = 1, completed_at = ?
                WHERE user_id IN (SELECT id FROM user_config WHERE confirmation_token = ?)
                AND step_name = 'email_confirmation'
            ''', (datetime.now(), token))

        conn.commit()
        conn.close()

        return rows_affected > 0

    def create_artist_profile(self, user_id: int, artist_name: str, folder_name: str = None, bio: str = None, license_type: str = 'free') -> Optional[int]:
        """Create a new artist profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check license limits
        cursor.execute('SELECT COUNT(*) FROM artist_profiles WHERE user_id = ? AND is_active = 1', (user_id,))
        artist_count = cursor.fetchone()[0]

        # Get or create license config
        cursor.execute('SELECT license_type, max_artists FROM license_config WHERE user_id = ?', (user_id,))
        license = cursor.fetchone()

        if license:
            max_artists = license[1]
        else:
            # Create default free license
            cursor.execute('''
                INSERT INTO license_config (user_id, license_type, max_artists)
                VALUES (?, 'free', 1)
            ''', (user_id,))
            max_artists = 1

        if artist_count >= max_artists:
            logger.warning(f"Artist limit reached: {artist_count}/{max_artists}")
            conn.close()
            return None

        # Generate folder name from artist name if not provided
        if not folder_name:
            import re
            folder_name = re.sub(r'[^a-z0-9]+', '_', artist_name.lower()).strip('_')

        # If this is the first artist, make it current
        is_current = (artist_count == 0)

        try:
            cursor.execute('''
                INSERT INTO artist_profiles (user_id, artist_name, folder_name, bio, is_current, license_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, artist_name, folder_name, bio, is_current, license_type))

            artist_id = cursor.lastrowid

            # Create artist folder structure (wallets will be subfolders)
            from pathlib import Path
            artist_folder = Path(f"knowledge_base/processed/artist_{folder_name}")
            artist_folder.mkdir(parents=True, exist_ok=True)

            media_folder = Path(f"knowledge_base/media/artist_{folder_name}")
            media_folder.mkdir(parents=True, exist_ok=True)

            conn.commit()
            logger.info(f"Created artist profile: {artist_name} (folder: artist_{folder_name})")
            return artist_id
        except sqlite3.IntegrityError:
            logger.warning(f"Artist folder already exists: {folder_name}")
            return None
        finally:
            conn.close()

    def add_minting_address(self, user_id: int, address: str, network: str = 'ethereum',
                           label: str = None, is_primary: bool = False, artist_name: str = None, artist_id: int = None) -> bool:
        """Add minting address with dedicated wallet folder"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get or create artist profile
        if not artist_id:
            if artist_name:
                # Create new artist profile for first address
                artist_id = self.create_artist_profile(user_id, artist_name)
                if not artist_id:
                    conn.close()
                    return False
            else:
                # Get current/first artist
                cursor.execute('SELECT id FROM artist_profiles WHERE user_id = ? AND is_current = 1 LIMIT 1', (user_id,))
                result = cursor.fetchone()
                if not result:
                    # Get any artist
                    cursor.execute('SELECT id FROM artist_profiles WHERE user_id = ? LIMIT 1', (user_id,))
                    result = cursor.fetchone()
                artist_id = result[0] if result else None

        if not artist_id:
            logger.error("No artist profile available")
            conn.close()
            return False

        # Check address limit for this artist (3 addresses per artist in free version)
        cursor.execute('SELECT COUNT(*) FROM minting_addresses WHERE artist_profile_id = ?', (artist_id,))
        address_count = cursor.fetchone()[0]

        cursor.execute('SELECT max_addresses FROM artist_profiles WHERE id = ?', (artist_id,))
        max_addresses = cursor.fetchone()[0]

        if address_count >= max_addresses:
            logger.warning(f"Address limit reached for artist: {address_count}/{max_addresses}")
            conn.close()
            return False

        # If this is the first address for this artist, make it primary
        if address_count == 0:
            is_primary = True

        # Generate unique folder name for this wallet
        address_short = address[:10].lower()
        address_folder = f"wallet_{address_short}"

        # Get artist folder name
        cursor.execute('SELECT folder_name FROM artist_profiles WHERE id = ?', (artist_id,))
        artist_folder_name = cursor.fetchone()[0]

        # Create wallet subfolder inside artist folder
        from pathlib import Path
        wallet_processed = Path(f"knowledge_base/processed/artist_{artist_folder_name}/{address_folder}")
        wallet_processed.mkdir(parents=True, exist_ok=True)

        wallet_media = Path(f"knowledge_base/media/artist_{artist_folder_name}/{address_folder}")
        wallet_media.mkdir(parents=True, exist_ok=True)

        try:
            # Normalize address: lowercase for Ethereum (case-insensitive), preserve case for others (Tezos is case-sensitive)
            normalized_address = address.lower() if network == 'ethereum' else address

            cursor.execute('''
                INSERT INTO minting_addresses (user_id, artist_profile_id, address, address_folder, network, label, is_primary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, artist_id, normalized_address, address_folder, network, label, is_primary))

            conn.commit()
            logger.info(f"Added wallet {address_short} for artist {artist_folder_name} -> {address_folder}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Address already exists: {address}")
            return False
        finally:
            conn.close()

    def get_minting_addresses(self, user_id: int) -> List[Dict]:
        """Get all minting addresses for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM minting_addresses
            WHERE user_id = ?
            ORDER BY is_primary DESC, created_at ASC
        ''', (user_id,))
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def complete_setup(self, user_id: int) -> bool:
        """Mark setup as complete for user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE user_config
            SET setup_completed = 1, setup_completed_at = ?, updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), datetime.now(), user_id))

        # Mark configuration complete step
        cursor.execute('''
            UPDATE setup_steps
            SET completed = 1, completed_at = ?
            WHERE user_id = ? AND step_name = 'configuration_complete'
        ''', (datetime.now(), user_id))

        conn.commit()
        conn.close()

        logger.info(f"Setup completed for user {user_id}")
        return True

    def get_primary_user(self) -> Optional[Dict]:
        """Get the primary (first) user with completed setup"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_config WHERE setup_completed = 1 LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_any_user(self) -> Optional[Dict]:
        """Get any user (including incomplete setup) - for resuming setup"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_config ORDER BY created_at DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_current_artist(self, user_id: int = None) -> Optional[Dict]:
        """Get the currently selected artist profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('SELECT * FROM artist_profiles WHERE user_id = ? AND is_current = 1', (user_id,))
        else:
            # Get for primary user
            cursor.execute('''
                SELECT ap.* FROM artist_profiles ap
                JOIN user_config uc ON ap.user_id = uc.id
                WHERE uc.setup_completed = 1 AND ap.is_current = 1
                LIMIT 1
            ''')

        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_all_artists(self, user_id: int = None) -> List[Dict]:
        """Get all artist profiles"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT ap.*, COUNT(ma.id) as address_count
                FROM artist_profiles ap
                LEFT JOIN minting_addresses ma ON ap.id = ma.artist_profile_id
                WHERE ap.user_id = ? AND ap.is_active = 1
                GROUP BY ap.id
                ORDER BY ap.created_at ASC
            ''', (user_id,))
        else:
            # Get for primary user
            cursor.execute('''
                SELECT ap.*, COUNT(ma.id) as address_count
                FROM artist_profiles ap
                JOIN user_config uc ON ap.user_id = uc.id
                LEFT JOIN minting_addresses ma ON ap.id = ma.artist_profile_id
                WHERE uc.setup_completed = 1 AND ap.is_active = 1
                GROUP BY ap.id
                ORDER BY ap.created_at ASC
            ''')

        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def switch_artist(self, artist_id: int) -> bool:
        """Switch to a different artist profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get the user_id for this artist
        cursor.execute('SELECT user_id FROM artist_profiles WHERE id = ?', (artist_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False

        user_id = result[0]

        # Set all artists for this user to not current
        cursor.execute('UPDATE artist_profiles SET is_current = 0 WHERE user_id = ?', (user_id,))

        # Set the selected artist to current
        cursor.execute('UPDATE artist_profiles SET is_current = 1 WHERE id = ?', (artist_id,))

        conn.commit()
        conn.close()

        logger.info(f"Switched to artist profile {artist_id}")
        return True

    def get_artist_folder_path(self, artist_id: int = None) -> str:
        """Get the folder path for an artist's data"""
        if artist_id:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT folder_name FROM artist_profiles WHERE id = ?', (artist_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return f"artist_{result[0]}"

        # Fallback: get current artist
        artist = self.get_current_artist()
        if artist:
            return f"artist_{artist['folder_name']}"

        return ""  # No artist-specific folder

    def get_wallet_folder_path(self, address_id: int = None, address: str = None) -> str:
        """Get full folder path for a specific wallet"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if address_id:
            cursor.execute('''
                SELECT ma.address_folder, ap.folder_name
                FROM minting_addresses ma
                JOIN artist_profiles ap ON ma.artist_profile_id = ap.id
                WHERE ma.id = ?
            ''', (address_id,))
        elif address:
            cursor.execute('''
                SELECT ma.address_folder, ap.folder_name
                FROM minting_addresses ma
                JOIN artist_profiles ap ON ma.artist_profile_id = ap.id
                WHERE ma.address = ?
            ''', (address.lower(),))
        else:
            conn.close()
            return ""

        result = cursor.fetchone()
        conn.close()

        if result:
            wallet_folder, artist_folder = result
            return f"artist_{artist_folder}/{wallet_folder}"

        return ""

    def upgrade_license(self, user_id: int, license_type: str, max_artists: int = None):
        """Upgrade user license (free → enterprise → white_label)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if license_type == 'free':
            max_artists = 1
        elif license_type == 'enterprise':
            max_artists = 5
        elif license_type == 'white_label':
            max_artists = max_artists or 999  # Custom limit

        cursor.execute('''
            UPDATE license_config
            SET license_type = ?, max_artists = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (license_type, max_artists, user_id))

        if cursor.rowcount == 0:
            # Create license if doesn't exist
            customer_service = (license_type in ['enterprise', 'white_label'])
            white_label_custom = (license_type == 'white_label')
            monthly_updates = (license_type == 'white_label')

            cursor.execute('''
                INSERT INTO license_config (user_id, license_type, max_artists, customer_service, white_label_custom, monthly_updates)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, license_type, max_artists, customer_service, white_label_custom, monthly_updates))

        conn.commit()
        conn.close()

        logger.info(f"Upgraded user {user_id} to {license_type} (max {max_artists} artists)")

    def sync_minting_addresses_to_blockchain_db(self):
        """Sync minting addresses to blockchain tracking database"""
        try:
            from collectors.blockchain_db import BlockchainDB
            blockchain_db = BlockchainDB()

            # Get primary user's minting addresses
            user = self.get_primary_user()
            if not user:
                return

            minting_addresses = self.get_minting_addresses(user['id'])

            conn = blockchain_db.get_connection()
            cursor = conn.cursor()

            for addr_data in minting_addresses:
                # Normalize address: lowercase for Ethereum (case-insensitive), preserve case for Tezos (case-sensitive)
                network = addr_data['network']
                normalized_address = addr_data['address'].lower() if network == 'ethereum' else addr_data['address']

                # Insert or update in blockchain tracking
                cursor.execute('''
                    INSERT INTO tracked_addresses (address, network, address_type, label, sync_enabled)
                    VALUES (?, ?, 'wallet', ?, 1)
                    ON CONFLICT(address) DO UPDATE SET
                        label = excluded.label,
                        address_type = 'wallet',
                        sync_enabled = 1
                ''', (normalized_address, network, addr_data['label'] or 'Minting Address'))

            conn.commit()
            conn.close()

            logger.info(f"Synced {len(minting_addresses)} minting addresses to blockchain database")
        except Exception as e:
            logger.error(f"Failed to sync minting addresses: {e}")
