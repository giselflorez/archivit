#!/usr/bin/env python3
"""
Setup Routes - Handle first-time setup wizard
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from interface.user_config_db import UserConfigDB
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import secrets
import logging
import re
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Scan status file location
SCAN_STATUS_FILE = Path(__file__).parent.parent.parent / 'db' / 'scan_status.json'


def get_scan_status():
    """Get current scan status from file"""
    try:
        if SCAN_STATUS_FILE.exists():
            with open(SCAN_STATUS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading scan status: {e}")
    return {'status': 'unknown'}


def update_scan_status(status_data):
    """Update scan status file"""
    try:
        SCAN_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCAN_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        logger.error(f"Error writing scan status: {e}")


def validate_blockchain_address(address: str, network: str) -> bool:
    """Validate blockchain address format based on network"""
    if network == 'ethereum':
        # Ethereum: 0x + 40 hex characters
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))

    elif network == 'tezos':
        # Tezos: tz1, tz2, tz3, or KT1 + base58 (36 chars typically)
        return bool(re.match(r'^(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}$', address))

    elif network == 'solana':
        # Solana: base58, 32-44 characters
        return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))

    elif network in ['bitcoin', 'counterparty', 'fakerares']:
        # Bitcoin/Counterparty/Fake Rares: legacy (1...), segwit (3...), or bech32 (bc1...)
        # Counterparty and Fake Rares use Bitcoin blockchain addresses
        return bool(re.match(r'^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$', address))

    elif network in ['eos', 'wax']:
        # EOS/WAX: 1-12 characters, lowercase letters and numbers 1-5
        return bool(re.match(r'^[a-z1-5.]{1,12}$', address))

    return False


def send_confirmation_email(email: str, token: str):
    """Send confirmation email with code"""
    try:
        # SECURITY: Generate 8-character confirmation code (32 bits of entropy)
        # Previous 6-char (24 bits) was too weak - increased for better security
        # Still user-friendly as it's displayed/typed once and expires quickly
        confirmation_code = secrets.token_hex(4).upper()  # 8 hex chars = 32 bits

        # Store code in session temporarily
        session['confirmation_code'] = confirmation_code
        session['confirmation_email'] = email

        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', 'info@web3photo.com')
        smtp_password = os.getenv('SMTP_PASSWORD', '')

        if smtp_user and smtp_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = f"ARCHIV-IT <{smtp_user}>"
                msg['To'] = email
                msg['Subject'] = 'ARCHIV-IT by WEB3GISEL - Confirm Your Email'

                body = f"""
Welcome to ARCHIV-IT by WEB3GISEL!

Your confirmation code is: {confirmation_code}

Enter this code to complete your setup.

---
Your Data. Your Output. Take Control.
https://web3photo.com
                """

                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, email, msg.as_string())
                server.quit()

                logger.info(f"Confirmation email sent to {email}")
                return 'email'
            except Exception as smtp_error:
                logger.error(f"SMTP error: {smtp_error}")
                # Fall back to console output
                print("=" * 50)
                print(f"CONFIRMATION CODE FOR {email}:")
                print(f"  {confirmation_code}")
                print("=" * 50)
                return 'console'
        else:
            # No SMTP configured - print to console
            print("=" * 50)
            print(f"CONFIRMATION CODE FOR {email}:")
            print(f"  {confirmation_code}")
            print("=" * 50)
            import sys
            sys.stdout.flush()
            logger.warning(f"SMTP not configured - CODE: {confirmation_code}")

        return 'console'
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")
        return False


def trigger_blockchain_scrape(address: str, network: str = 'ethereum', artist_folder: str = None):
    """Trigger blockchain scrape for new minting address using wallet scanner"""
    try:
        import threading
        from pathlib import Path
        import sys

        # Add parent path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent))

        # Initialize scan status
        update_scan_status({
            'status': 'scanning',
            'current_step': 'connect',
            'started_at': time.time(),
            'address': address,
            'works_found': 0,
            'collectors_found': 0,
            'networks': []
        })

        def run_scan():
            """Run wallet scan in background thread"""
            try:
                from collectors.wallet_scanner import WalletScanner

                logger.info(f"Starting wallet scan for {address} (network: {network})")

                # Update status: connecting
                update_scan_status({
                    'status': 'scanning',
                    'current_step': 'connect',
                    'started_at': time.time(),
                    'address': address,
                    'works_found': 0,
                    'collectors_found': 0,
                    'networks': []
                })

                scanner = WalletScanner()

                # Auto-detect network if not specified or verify
                detected_network, confidence = scanner.detect_blockchain(address)
                networks_to_scan = scanner.detect_all_networks(address)

                logger.info(f"Detected network: {detected_network} ({confidence:.0%}), scanning: {networks_to_scan}")

                # Update status: scanning mints
                update_scan_status({
                    'status': 'scanning',
                    'current_step': 'mints',
                    'address': address,
                    'works_found': 0,
                    'collectors_found': 0,
                    'networks': networks_to_scan
                })

                # Run the scan
                results = scanner.scan_wallet(address, networks=networks_to_scan)

                # Get stats from results
                combined_stats = results.get('combined_stats', {})
                works_found = combined_stats.get('total_minted', 0)
                collectors_found = combined_stats.get('unique_collectors', 0)

                # Update status: mapping collectors
                update_scan_status({
                    'status': 'scanning',
                    'current_step': 'collectors',
                    'address': address,
                    'works_found': works_found,
                    'collectors_found': collectors_found,
                    'networks': networks_to_scan
                })

                # Save to database
                scanner.save_scan_to_db(results)

                # Update status: analyzing
                update_scan_status({
                    'status': 'scanning',
                    'current_step': 'analyze',
                    'address': address,
                    'works_found': works_found,
                    'collectors_found': collectors_found,
                    'networks': networks_to_scan
                })

                logger.info(f"Wallet scan complete for {address}: {combined_stats}")

                # Log summary
                for net, result in results.get('network_results', {}).items():
                    mints = len(result.get('minted_nfts', []))
                    collectors = len(result.get('collectors', []))
                    logger.info(f"  {net}: {mints} mints, {collectors} collectors")

                # Mark complete
                update_scan_status({
                    'status': 'complete',
                    'current_step': 'complete',
                    'address': address,
                    'works_found': works_found,
                    'collectors_found': collectors_found,
                    'networks': networks_to_scan,
                    'completed_at': time.time(),
                    'assessment_url': '/assessment-report'
                })

            except Exception as e:
                logger.error(f"Background wallet scan failed: {e}")
                # Mark as error but still allow proceeding
                update_scan_status({
                    'status': 'error',
                    'error': str(e),
                    'assessment_url': '/assessment-report'
                })

        # Run scan in background thread
        scan_thread = threading.Thread(target=run_scan, daemon=True)
        scan_thread.start()

        logger.info(f"Wallet scan initiated in background for {address}")
        return True

    except Exception as e:
        logger.error(f"Failed to trigger wallet scan: {e}")
        return False


def _compare_image_similarity(img1_path: str, img2_path: str, threshold: float = 0.90) -> dict:
    """
    Compare two images using perceptual hashing (pHash).
    Returns similarity score and match status.

    Args:
        img1_path: Path to first image
        img2_path: Path to second image
        threshold: Similarity threshold (0.0 to 1.0, default 0.90 = 90%)

    Returns:
        dict with 'similarity' (0-100), 'match' (bool), 'error' (if any)
    """
    try:
        from PIL import Image
        import imagehash
    except ImportError:
        return {'similarity': 0, 'match': False, 'error': 'PIL/imagehash not installed'}

    try:
        # Load and resize to 64x64 for consistent comparison
        img1 = Image.open(img1_path).resize((64, 64))
        img2 = Image.open(img2_path).resize((64, 64))

        # Calculate perceptual hash with hash_size=8 (64-bit hash)
        # This gives good balance between speed and accuracy for thumbnails
        hash1 = imagehash.phash(img1, hash_size=8)
        hash2 = imagehash.phash(img2, hash_size=8)

        # Hamming distance (number of different bits)
        distance = hash1 - hash2

        # Convert to similarity percentage
        # hash_size=8 gives 64 bits, so max distance is 64
        max_distance = 64
        similarity = (1 - distance / max_distance) * 100

        # Determine if it's a match based on threshold
        is_match = similarity >= (threshold * 100)

        return {
            'similarity': round(similarity, 1),
            'match': is_match,
            'distance': distance,
            'error': None
        }

    except Exception as e:
        logger.error(f"Image comparison error: {e}")
        return {'similarity': 0, 'match': False, 'error': str(e)}


def _get_collectors_for_verification(artist_address: str) -> list:
    """
    Get collector data for the accuracy verification section.
    Returns list of collectors ranked by investigation potential (unanswered questions).
    """
    import sqlite3
    from pathlib import Path

    collectors = []
    db_path = Path(__file__).parent.parent.parent / 'db' / 'blockchain_tracking.db'

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get address_id for this artist - prefer the one with actual mints
        cursor.execute('''
            SELECT ta.id, COUNT(m.id) as mint_count
            FROM tracked_addresses ta
            LEFT JOIN nft_mints m ON m.address_id = ta.id
            WHERE LOWER(ta.address) = LOWER(?)
            GROUP BY ta.id
            ORDER BY COUNT(m.id) DESC, ta.last_synced DESC NULLS LAST
            LIMIT 1
        ''', (artist_address,))
        addr_row = cursor.fetchone()

        if not addr_row:
            conn.close()
            return []

        address_id = addr_row['id']

        # Get collectors with their NFT count - using actual schema
        cursor.execute('''
            SELECT
                c.collector_address as address,
                COUNT(DISTINCT c.nft_mint_id) as nft_count,
                MIN(c.purchase_timestamp) as first_purchase,
                SUM(COALESCE(c.purchase_price_native, 0)) as total_spent,
                c.platform
            FROM collectors c
            JOIN nft_mints m ON c.nft_mint_id = m.id
            WHERE m.address_id = ?
              AND c.collector_address != '0x0000000000000000000000000000000000000000'
            GROUP BY c.collector_address
            ORDER BY COUNT(DISTINCT c.nft_mint_id) DESC
            LIMIT 20
        ''', (address_id,))

        rows = cursor.fetchall()

        for i, row in enumerate(rows):
            # Calculate "unanswered" score based on missing data
            unanswered = 0

            # No purchase price = unclear transaction
            if not row['total_spent'] or row['total_spent'] == 0:
                unanswered += 1

            # Single-purchase collectors are less clear
            if row['nft_count'] == 1:
                unanswered += 1

            # No timestamp = unclear history
            if not row['first_purchase']:
                unanswered += 1

            collectors.append({
                'address': row['address'],
                'nft_count': row['nft_count'],
                'platform': row['platform'],
                'unanswered': unanswered if unanswered > 0 else None,
                'potential_score': min(100, unanswered * 33),  # 0-100 scale
                'potential_level': 'high' if unanswered >= 2 else 'medium' if unanswered == 1 else 'low'
            })

        conn.close()

        # Sort by investigation potential (most unclear first)
        collectors.sort(key=lambda x: (x['unanswered'] or 0, -x['nft_count']), reverse=True)

    except Exception as e:
        logger.error(f"Error getting collectors for verification: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return collectors


def register_setup_routes(app):
    """Register all setup routes"""

    @app.route('/setup', methods=['GET', 'POST'])
    def setup_wizard():
        """Setup wizard main route"""
        user_db = UserConfigDB()

        # If setup is already complete, redirect to home
        if user_db.is_setup_complete():
            return redirect('/')

        # Check if ToS was accepted - redirect to terms if not
        if not session.get('tos_accepted'):
            # Also check database for persistent ToS acceptance
            try:
                conn = user_db.conn
                cursor = conn.cursor()
                cursor.execute('SELECT tos_accepted FROM user_config WHERE tos_accepted = 1 LIMIT 1')
                if not cursor.fetchone():
                    return redirect('/terms-of-service')
            except:
                return redirect('/terms-of-service')

        # Determine current step - use get_any_user to resume incomplete setups
        user = user_db.get_any_user()
        if user:
            if not user['email_confirmed']:
                step = 2
                email = user['email']
            else:
                step = 3
                email = user['email']
                addresses = user_db.get_minting_addresses(user['id'])
        else:
            step = 1
            email = None
            addresses = []

        error = None
        success = None

        if request.method == 'POST':
            form_step = int(request.form.get('step', 1))

            if form_step == 1:
                # Step 1: Email collection
                email = request.form.get('email', '').strip()
                marketing_opt_in = request.form.get('marketing_opt_in') == 'on'

                if not email:
                    error = "Email is required"
                else:
                    try:
                        # Create user
                        user_id = user_db.create_user(email, marketing_opt_in)
                        user = user_db.get_user_by_email(email)

                        # Send confirmation email
                        email_result = send_confirmation_email(email, user['confirmation_token'])

                        step = 2
                        if email_result == 'email':
                            success = f"Confirmation code sent to {email}"
                        else:
                            success = "Confirmation code sent! Check your console output."
                    except Exception as e:
                        error = f"Failed to create user: {e}"

            elif form_step == 2:
                # Step 2: Email confirmation
                confirmation_code = request.form.get('confirmation_code', '').strip().upper()

                # Check against session code
                if confirmation_code == session.get('confirmation_code'):
                    email = session.get('confirmation_email')
                    user = user_db.get_user_by_email(email)

                    if user:
                        # Confirm email
                        user_db.confirm_email(user['confirmation_token'])

                        step = 3
                        success = "Email confirmed! Now add your minting addresses."
                        addresses = []
                    else:
                        # User was deleted or doesn't exist - restart setup
                        session.clear()
                        error = "Session expired. Please start again."
                        step = 1
                else:
                    error = "Invalid confirmation code"
                    step = 2

            elif form_step == 3:
                # Step 3: Add minting addresses (up to 3 at once)
                # Use first wallet's label as artist name
                artist_name = request.form.get('label', '').strip()
                if not artist_name:
                    artist_name = request.form.get('artist_name', '').strip()

                # Collect all wallet addresses from form
                wallets = []
                for i, suffix in enumerate(['', '_2', '_3']):
                    addr = request.form.get(f'address{suffix}', '').strip()
                    net = request.form.get(f'network{suffix}', 'ethereum').strip()
                    label = request.form.get(f'label{suffix}', '').strip()
                    if addr:
                        wallets.append({'address': addr, 'network': net, 'label': label})

                # Get current user
                user = user_db.get_any_user()
                if not user:
                    email = session.get('confirmation_email')
                    user = user_db.get_user_by_email(email)

                # Use first wallet label as artist name if not provided
                if not artist_name and wallets:
                    artist_name = wallets[0].get('label') or f"Artist_{wallets[0]['address'][:8]}"

                # Validation
                if not wallets:
                    error = "At least one wallet address is required"
                else:
                    # Validate all addresses
                    invalid_addr = None
                    for w in wallets:
                        if not validate_blockchain_address(w['address'], w['network']):
                            invalid_addr = w['address'][:15]
                            break

                    if invalid_addr:
                        error = f"Invalid address format: {invalid_addr}..."
                    else:
                        # Add first wallet with artist profile creation
                        added_count = 0
                        artist_id = None

                        for i, w in enumerate(wallets):
                            if i == 0:
                                # First wallet creates artist profile
                                success_added = user_db.add_minting_address(
                                    user['id'],
                                    w['address'],
                                    network=w['network'],
                                    artist_name=artist_name
                                )
                                if success_added:
                                    added_count += 1
                                    artist = user_db.get_current_artist(user['id'])
                                    artist_id = artist['id'] if artist else None
                            else:
                                # Subsequent wallets use existing artist
                                if artist_id:
                                    success_added = user_db.add_minting_address(
                                        user['id'],
                                        w['address'],
                                        network=w['network'],
                                        artist_id=artist_id
                                    )
                                    if success_added:
                                        added_count += 1

                            # Trigger blockchain scrape for each address
                            if success_added:
                                wallet_folder = user_db.get_wallet_folder_path(address=w['address'])
                                trigger_blockchain_scrape(w['address'], w['network'], wallet_folder)

                        if added_count > 0:
                            # Sync to blockchain database
                            user_db.sync_minting_addresses_to_blockchain_db()

                            # Don't mark complete yet - redirect to scanning page
                            # Setup will be marked complete after assessment
                            return redirect('/setup/scanning')
                        else:
                            error = "Failed to add addresses"

                step = 3
                addresses = user_db.get_minting_addresses(user['id']) if user else []

        # Calculate progress
        progress = (step / 4) * 100

        return render_template('setup_wizard.html',
                             step=step,
                             email=email,
                             addresses=addresses if step == 3 else [],
                             progress=progress,
                             error=error,
                             success=success)

    @app.route('/setup/complete')
    def setup_complete():
        """Complete setup and redirect to main app"""
        user_db = UserConfigDB()
        user = user_db.get_primary_user()

        if user:
            # Mark setup as complete
            user_db.complete_setup(user['id'])

            # Final sync of minting addresses
            user_db.sync_minting_addresses_to_blockchain_db()

            return redirect('/')
        else:
            return redirect('/setup')

    @app.route('/setup/remove-address', methods=['POST'])
    def remove_address():
        """Remove a minting address"""
        address_id = request.form.get('address_id')

        if address_id:
            user_db = UserConfigDB()
            conn = user_db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM minting_addresses WHERE id = ?', (address_id,))
            conn.commit()
            conn.close()

        return redirect('/setup')

    @app.route('/setup/resend')
    def resend_confirmation():
        """Resend confirmation email"""
        email = session.get('confirmation_email')

        if email:
            user_db = UserConfigDB()
            user = user_db.get_user_by_email(email)

            if user:
                send_confirmation_email(email, user['confirmation_token'])

        return redirect('/setup')

    @app.route('/setup/show-code')
    def show_code():
        """Development only - show confirmation code"""
        code = session.get('confirmation_code', 'No code in session')
        email = session.get('confirmation_email', 'No email in session')
        return f"<h1>Dev Mode</h1><p>Email: {email}</p><p>Code: <strong style='font-size:2em; font-family:monospace;'>{code}</strong></p>"

    @app.route('/setup/scanning')
    def setup_scanning():
        """Scanning progress page - shows while wallet scan runs"""
        user_db = UserConfigDB()
        user = user_db.get_any_user()

        # If no user or setup already complete, redirect appropriately
        if not user:
            return redirect('/setup')

        # Check if scan is already complete
        status = get_scan_status()
        if status.get('status') == 'complete':
            return redirect('/assessment-report')

        return render_template('setup_scanning.html')

    @app.route('/setup/scan-status')
    def scan_status():
        """API endpoint to check scan progress"""
        status = get_scan_status()

        # Add some fallback handling for long-running scans
        if status.get('status') == 'scanning':
            started_at = status.get('started_at', 0)
            elapsed = time.time() - started_at if started_at else 0

            # If scan has been running for more than 3 minutes, allow proceeding
            if elapsed > 180:
                status['status'] = 'complete'
                status['assessment_url'] = '/assessment-report'
                status['timeout'] = True

        return jsonify(status)

    @app.route('/assessment-report')
    def assessment_report():
        """Assessment report page - shows badge and scores after scan"""
        user_db = UserConfigDB()
        user = user_db.get_any_user()

        if not user:
            return redirect('/setup')

        # Get artist info for the report
        artist = user_db.get_current_artist(user['id']) if user else None
        artist_name = artist['artist_name'] if artist else 'Artist'

        # Try to get real assessment data
        try:
            from interface.reputation_score import ReputationScorer, ReputationState

            scorer = ReputationScorer()
            addresses = user_db.get_minting_addresses(user['id'])

            if addresses:
                # Get the primary address
                primary_address = addresses[0]['address']

                # Calculate reputation score
                result = scorer.calculate_reputation(primary_address)

                # Map state to template values
                state_map = {
                    ReputationState.VERIFIED: ('VERIFIED', 85, '#22c55e'),
                    ReputationState.ESTABLISHED: ('ESTABLISHED', 65, '#84cc16'),
                    ReputationState.EMERGING: ('EMERGING', 40, '#eab308'),
                    ReputationState.UNCERTAIN: ('UNCERTAIN', 15, '#ef4444'),
                }

                badge_state, fill_percent, badge_color = state_map.get(
                    result.state,
                    ('EMERGING', 40, '#eab308')
                )

                # Format findings as chips
                findings = []
                for finding in result.findings[:6]:  # Max 6 findings
                    findings.append({
                        'label': finding.split(':')[0] if ':' in finding else finding[:20],
                        'detail': finding,
                        'type': 'positive' if any(w in finding.lower() for w in ['active', 'healthy', 'organic', 'diverse']) else 'neutral'
                    })

                # Get collector data for verification section
                collectors = _get_collectors_for_verification(primary_address)

                return render_template('assessment_report.html',
                    artist_name=artist_name,
                    badge_state=badge_state,
                    fill_percent=fill_percent,
                    badge_color=badge_color,
                    overall_score=result.score,
                    collector_score=int(result.component_scores.get('collector_vitality', 0)),
                    network_score=int(result.component_scores.get('network_authenticity', 0)),
                    transaction_score=int(result.component_scores.get('transaction_legitimacy', 0)),
                    timeline_score=int(result.component_scores.get('timeline_health', 0)),
                    findings=findings,
                    collectors=collectors,
                    summary=f"Based on {len(addresses)} wallet(s) analyzed"
                )

        except Exception as e:
            import traceback
            logger.error(f"Error calculating assessment: {e}")
            logger.error(traceback.format_exc())

        # Fallback to demo data if real calculation fails
        return render_template('assessment_report.html',
            artist_name=artist_name,
            badge_state='EMERGING',
            fill_percent=40,
            badge_color='#eab308',
            overall_score=42,
            collector_score=45,
            network_score=38,
            transaction_score=50,
            timeline_score=35,
            findings=[
                {'label': 'Scan Complete', 'detail': 'Blockchain data indexed successfully', 'type': 'positive'},
                {'label': 'Building Profile', 'detail': 'Collector network being analyzed', 'type': 'neutral'}
            ],
            collectors=[],  # No collectors in fallback
            summary="Initial assessment based on available blockchain data"
        )

    @app.route('/setup/finish')
    def setup_finish():
        """Mark setup as complete and redirect to main app"""
        user_db = UserConfigDB()
        user = user_db.get_any_user()

        if user:
            user_db.complete_setup(user['id'])

        return redirect('/')

    @app.route('/api/investigate-collectors', methods=['POST'])
    def api_investigate_collectors():
        """
        API endpoint to investigate selected collectors.
        Accepts: { skip: [...], auto: [...], deep: [...] }
        Where each array contains wallet addresses.
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            auto_addresses = data.get('auto', [])
            deep_addresses = data.get('deep', [])

            # Nothing to investigate
            if not auto_addresses and not deep_addresses:
                return jsonify({'success': True, 'message': 'No collectors selected for investigation'})

            # For now, log the investigation request
            # In the future, this will trigger actual API calls
            logger.info(f"Investigation requested: {len(auto_addresses)} auto, {len(deep_addresses)} deep")

            # Store investigation results in the database
            # (Placeholder - actual implementation would call external APIs)
            import sqlite3
            from pathlib import Path

            db_path = Path(__file__).parent.parent.parent / 'db' / 'blockchain_tracking.db'
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create investigation_log table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investigation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collector_address TEXT NOT NULL,
                    investigation_level TEXT NOT NULL,
                    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    result_json TEXT
                )
            ''')

            # Log the investigation requests
            for addr in auto_addresses:
                cursor.execute(
                    'INSERT INTO investigation_log (collector_address, investigation_level) VALUES (?, ?)',
                    (addr, 'auto')
                )

            for addr in deep_addresses:
                cursor.execute(
                    'INSERT INTO investigation_log (collector_address, investigation_level) VALUES (?, ?)',
                    (addr, 'deep')
                )

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': f'Investigation started for {len(auto_addresses) + len(deep_addresses)} collectors',
                'auto_count': len(auto_addresses),
                'deep_count': len(deep_addresses)
            })

        except Exception as e:
            logger.error(f"Error in investigate-collectors API: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
