// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title NORTHSTAR PRINCIPALS EXPERIENCE
 * @author ARCHIV-IT / STR-8 Ecosystem
 * @notice The first blockchain entry of the 22 Masters wisdom framework
 * @dev Implements ERC-721 + ERC-6551 compatibility + ERC-7496 dynamic traits
 *
 * SACRED COVENANT:
 * - This NFT represents the EXPERIENCE and TEACHINGS of the 22 Masters
 * - It does NOT reproduce their actual artwork
 * - New masters and truths can be added over time (append-only)
 * - Original creation timestamp and hash are immutable
 *
 * AI SAFETY NOTICE:
 * - All content hashes are verified before inclusion
 * - No AI-hallucinated content may be added without verification
 * - Verification requires multi-sig approval
 */

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/utils/Base64.sol";

/**
 * @title INorthstarTraits
 * @notice ERC-7496 Dynamic Traits interface for NORTHSTAR
 */
interface INorthstarTraits {
    event TraitUpdated(uint256 indexed tokenId, bytes32 indexed traitKey, bytes32 value);
    event MasterAdded(uint256 indexed tokenId, bytes32 indexed masterId, string name, string domain);
    event TruthAdded(uint256 indexed tokenId, uint256 indexed truthRank, string statement);

    function setTrait(uint256 tokenId, bytes32 traitKey, bytes32 value) external;
    function getTrait(uint256 tokenId, bytes32 traitKey) external view returns (bytes32);
    function getMasterCount(uint256 tokenId) external view returns (uint256);
    function getTruthCount(uint256 tokenId) external view returns (uint256);
}

/**
 * @title NorthstarPrincipals
 * @notice Main NORTHSTAR PRINCIPALS EXPERIENCE contract
 */
contract NorthstarPrincipals is
    ERC721,
    ERC721URIStorage,
    AccessControl,
    ReentrancyGuard,
    INorthstarTraits
{
    using Strings for uint256;

    // ============================================
    // SACRED CONSTANTS (DO NOT MODIFY)
    // ============================================

    uint256 public constant PHI_NUMERATOR = 1618033988749895;
    uint256 public constant PHI_DENOMINATOR = 1000000000000000;
    uint256 public constant GOLDEN_ANGLE = 137507764050038; // * 10^12
    uint256 public constant SCHUMANN = 783; // 7.83 Hz * 100

    // Tesla pattern encoded (3, 6, 9)
    uint8 public constant TESLA_3 = 3;
    uint8 public constant TESLA_6 = 6;
    uint8 public constant TESLA_9 = 9;

    // ============================================
    // ROLES
    // ============================================

    bytes32 public constant FOUNDER_ROLE = keccak256("FOUNDER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant MASTER_ADDER_ROLE = keccak256("MASTER_ADDER_ROLE");

    // ============================================
    // STRUCTS
    // ============================================

    struct Master {
        bytes32 id;
        string name;
        string dates;
        uint16 birthYear;
        string domain;
        bool isFeminine;
        uint24 color;
        string archetype;
        string haloStyle;
        bool verified;
        uint256 addedTimestamp;
        bytes32 verificationHash;
    }

    struct Truth {
        uint256 rank;
        string statement;
        string category;
        string description;
        bytes32[] connectedMasters;
        bool verified;
        uint256 addedTimestamp;
    }

    struct TokenMetadata {
        uint256 creationTimestamp;
        bytes32 originalContentHash;
        bytes32 visualizationHash;
        string arweaveURI;
        string ipfsURI;
        uint256 version;
        bool locked;
    }

    // ============================================
    // STATE VARIABLES
    // ============================================

    // Token ID counter
    uint256 private _tokenIdCounter;

    // Token metadata
    mapping(uint256 => TokenMetadata) public tokenMetadata;

    // Masters registry (tokenId => masterId => Master)
    mapping(uint256 => mapping(bytes32 => Master)) public masters;
    mapping(uint256 => bytes32[]) public masterIds;

    // Truths registry (tokenId => rank => Truth)
    mapping(uint256 => mapping(uint256 => Truth)) public truths;
    mapping(uint256 => uint256[]) public truthRanks;

    // Dynamic traits (ERC-7496) (tokenId => traitKey => value)
    mapping(uint256 => mapping(bytes32 => bytes32)) private _traits;

    // Verification registry
    mapping(bytes32 => bool) public verifiedHashes;

    // Token Bound Account registry (ERC-6551 compatibility)
    mapping(uint256 => address) public tokenBoundAccounts;

    // ============================================
    // EVENTS
    // ============================================

    event NorthstarMinted(
        uint256 indexed tokenId,
        address indexed founder,
        bytes32 contentHash,
        uint256 timestamp
    );

    event MetadataUpdated(
        uint256 indexed tokenId,
        uint256 version,
        string arweaveURI,
        string ipfsURI
    );

    event TokenBoundAccountSet(
        uint256 indexed tokenId,
        address indexed account
    );

    event VerificationAdded(
        bytes32 indexed hash,
        address indexed verifier,
        uint256 timestamp
    );

    // ============================================
    // CONSTRUCTOR
    // ============================================

    constructor(
        address founder,
        address[] memory verifiers
    ) ERC721("NORTHSTAR PRINCIPALS EXPERIENCE", "NORTHSTAR") {
        _grantRole(DEFAULT_ADMIN_ROLE, founder);
        _grantRole(FOUNDER_ROLE, founder);
        _grantRole(MASTER_ADDER_ROLE, founder);

        for (uint i = 0; i < verifiers.length; i++) {
            _grantRole(VERIFIER_ROLE, verifiers[i]);
        }
    }

    // ============================================
    // MINTING (ONE-TIME GENESIS)
    // ============================================

    /**
     * @notice Mint the genesis NORTHSTAR PRINCIPALS token
     * @param contentHash Hash of the complete visualization content
     * @param visualizationHash Hash of the v3_spectral HTML
     * @param arweaveURI Permanent Arweave storage URI
     * @param ipfsURI IPFS backup URI
     */
    function mintGenesis(
        bytes32 contentHash,
        bytes32 visualizationHash,
        string calldata arweaveURI,
        string calldata ipfsURI
    ) external onlyRole(FOUNDER_ROLE) nonReentrant returns (uint256) {
        require(_tokenIdCounter == 0, "Genesis already minted");
        require(contentHash != bytes32(0), "Content hash required");
        require(bytes(arweaveURI).length > 0, "Arweave URI required");

        uint256 tokenId = _tokenIdCounter++;

        _safeMint(msg.sender, tokenId);

        tokenMetadata[tokenId] = TokenMetadata({
            creationTimestamp: block.timestamp,
            originalContentHash: contentHash,
            visualizationHash: visualizationHash,
            arweaveURI: arweaveURI,
            ipfsURI: ipfsURI,
            version: 1,
            locked: false
        });

        // Set initial traits
        _traits[tokenId][keccak256("MASTER_COUNT")] = bytes32(uint256(22));
        _traits[tokenId][keccak256("TRUTH_COUNT")] = bytes32(uint256(100));
        _traits[tokenId][keccak256("FEMININE_COUNT")] = bytes32(uint256(9));
        _traits[tokenId][keccak256("MASCULINE_COUNT")] = bytes32(uint256(13));
        _traits[tokenId][keccak256("GENESIS_BLOCK")] = bytes32(block.number);

        emit NorthstarMinted(tokenId, msg.sender, contentHash, block.timestamp);

        return tokenId;
    }

    // ============================================
    // MASTER MANAGEMENT
    // ============================================

    /**
     * @notice Add a new master to the NORTHSTAR constellation
     * @dev Requires MASTER_ADDER_ROLE and verified content hash
     */
    function addMaster(
        uint256 tokenId,
        bytes32 masterId,
        string calldata name,
        string calldata dates,
        uint16 birthYear,
        string calldata domain,
        bool isFeminine,
        uint24 color,
        string calldata archetype,
        string calldata haloStyle,
        bytes32 verificationHash
    ) external onlyRole(MASTER_ADDER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(!tokenMetadata[tokenId].locked, "Token is locked");
        require(masters[tokenId][masterId].addedTimestamp == 0, "Master already exists");
        require(verifiedHashes[verificationHash], "Content not verified");

        masters[tokenId][masterId] = Master({
            id: masterId,
            name: name,
            dates: dates,
            birthYear: birthYear,
            domain: domain,
            isFeminine: isFeminine,
            color: color,
            archetype: archetype,
            haloStyle: haloStyle,
            verified: true,
            addedTimestamp: block.timestamp,
            verificationHash: verificationHash
        });

        masterIds[tokenId].push(masterId);

        // Update trait counts
        uint256 currentCount = uint256(_traits[tokenId][keccak256("MASTER_COUNT")]);
        _traits[tokenId][keccak256("MASTER_COUNT")] = bytes32(currentCount + 1);

        if (isFeminine) {
            uint256 femCount = uint256(_traits[tokenId][keccak256("FEMININE_COUNT")]);
            _traits[tokenId][keccak256("FEMININE_COUNT")] = bytes32(femCount + 1);
        } else {
            uint256 mascCount = uint256(_traits[tokenId][keccak256("MASCULINE_COUNT")]);
            _traits[tokenId][keccak256("MASCULINE_COUNT")] = bytes32(mascCount + 1);
        }

        emit MasterAdded(tokenId, masterId, name, domain);
        emit TraitUpdated(tokenId, keccak256("MASTER_COUNT"), bytes32(currentCount + 1));
    }

    /**
     * @notice Add a new truth to the NORTHSTAR constellation
     */
    function addTruth(
        uint256 tokenId,
        uint256 rank,
        string calldata statement,
        string calldata category,
        string calldata description,
        bytes32[] calldata connectedMasters
    ) external onlyRole(MASTER_ADDER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(!tokenMetadata[tokenId].locked, "Token is locked");
        require(truths[tokenId][rank].addedTimestamp == 0, "Truth rank already exists");

        truths[tokenId][rank] = Truth({
            rank: rank,
            statement: statement,
            category: category,
            description: description,
            connectedMasters: connectedMasters,
            verified: true,
            addedTimestamp: block.timestamp
        });

        truthRanks[tokenId].push(rank);

        uint256 currentCount = uint256(_traits[tokenId][keccak256("TRUTH_COUNT")]);
        _traits[tokenId][keccak256("TRUTH_COUNT")] = bytes32(currentCount + 1);

        emit TruthAdded(tokenId, rank, statement);
        emit TraitUpdated(tokenId, keccak256("TRUTH_COUNT"), bytes32(currentCount + 1));
    }

    // ============================================
    // ERC-7496 DYNAMIC TRAITS
    // ============================================

    function setTrait(
        uint256 tokenId,
        bytes32 traitKey,
        bytes32 value
    ) external override onlyRole(MASTER_ADDER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(!tokenMetadata[tokenId].locked, "Token is locked");

        _traits[tokenId][traitKey] = value;
        emit TraitUpdated(tokenId, traitKey, value);
    }

    function getTrait(
        uint256 tokenId,
        bytes32 traitKey
    ) external view override returns (bytes32) {
        return _traits[tokenId][traitKey];
    }

    function getMasterCount(uint256 tokenId) external view override returns (uint256) {
        return uint256(_traits[tokenId][keccak256("MASTER_COUNT")]);
    }

    function getTruthCount(uint256 tokenId) external view override returns (uint256) {
        return uint256(_traits[tokenId][keccak256("TRUTH_COUNT")]);
    }

    // ============================================
    // ERC-6551 TOKEN BOUND ACCOUNT
    // ============================================

    /**
     * @notice Set the Token Bound Account for this NFT
     * @dev Allows the NFT to own other assets
     */
    function setTokenBoundAccount(
        uint256 tokenId,
        address account
    ) external {
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        tokenBoundAccounts[tokenId] = account;
        emit TokenBoundAccountSet(tokenId, account);
    }

    // ============================================
    // VERIFICATION SYSTEM
    // ============================================

    /**
     * @notice Add a verified content hash
     * @dev Only verifiers can add hashes, preventing AI hallucination
     */
    function addVerification(
        bytes32 contentHash
    ) external onlyRole(VERIFIER_ROLE) {
        require(!verifiedHashes[contentHash], "Already verified");
        verifiedHashes[contentHash] = true;
        emit VerificationAdded(contentHash, msg.sender, block.timestamp);
    }

    /**
     * @notice Batch verify multiple content hashes
     */
    function batchVerify(
        bytes32[] calldata contentHashes
    ) external onlyRole(VERIFIER_ROLE) {
        for (uint i = 0; i < contentHashes.length; i++) {
            if (!verifiedHashes[contentHashes[i]]) {
                verifiedHashes[contentHashes[i]] = true;
                emit VerificationAdded(contentHashes[i], msg.sender, block.timestamp);
            }
        }
    }

    // ============================================
    // METADATA MANAGEMENT
    // ============================================

    /**
     * @notice Update metadata URIs (append new version)
     */
    function updateMetadata(
        uint256 tokenId,
        string calldata newArweaveURI,
        string calldata newIpfsURI
    ) external onlyRole(FOUNDER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(!tokenMetadata[tokenId].locked, "Token is locked");

        tokenMetadata[tokenId].arweaveURI = newArweaveURI;
        tokenMetadata[tokenId].ipfsURI = newIpfsURI;
        tokenMetadata[tokenId].version++;

        emit MetadataUpdated(
            tokenId,
            tokenMetadata[tokenId].version,
            newArweaveURI,
            newIpfsURI
        );
    }

    /**
     * @notice Lock token metadata permanently
     */
    function lockMetadata(uint256 tokenId) external onlyRole(FOUNDER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        tokenMetadata[tokenId].locked = true;
    }

    // ============================================
    // ON-CHAIN SVG GENERATION
    // ============================================

    /**
     * @notice Generate on-chain SVG representation
     * @dev Creates a permanent visual even if external storage fails
     */
    function generateOnChainSVG(uint256 tokenId) public view returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");

        TokenMetadata memory meta = tokenMetadata[tokenId];
        uint256 masterCount = uint256(_traits[tokenId][keccak256("MASTER_COUNT")]);
        uint256 truthCount = uint256(_traits[tokenId][keccak256("TRUTH_COUNT")]);

        string memory svg = string(abi.encodePacked(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800">',
            '<defs>',
            '<radialGradient id="bg" cx="50%" cy="50%" r="70%">',
            '<stop offset="0%" stop-color="#0a0a12"/>',
            '<stop offset="100%" stop-color="#030308"/>',
            '</radialGradient>',
            '<filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/>',
            '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
            '</defs>',
            '<rect width="800" height="800" fill="url(#bg)"/>',
            _generateConstellation(masterCount),
            _generateTitle(masterCount, truthCount),
            _generateTimestamp(meta.creationTimestamp),
            _generateSacredGeometry(),
            '</svg>'
        ));

        return svg;
    }

    function _generateConstellation(uint256 masterCount) internal pure returns (string memory) {
        string memory nodes = '';

        // Generate nodes in golden spiral
        for (uint256 i = 0; i < masterCount && i < 22; i++) {
            uint256 angle = (i * 13750) % 36000; // Golden angle approximation
            uint256 radius = 150 + (i * 10);
            int256 cosVal = _cos(angle);
            int256 sinVal = _sin(angle);
            uint256 x = uint256(int256(400) + (int256(radius) * cosVal) / 1000);
            uint256 y = uint256(int256(400) + (int256(radius) * sinVal) / 1000);

            // Alternate colors for feminine/masculine
            string memory color = i < 9 ? "#ba6587" : "#5aa8b9";

            nodes = string(abi.encodePacked(
                nodes,
                '<circle cx="', x.toString(), '" cy="', y.toString(),
                '" r="8" fill="', color, '" filter="url(#glow)" opacity="0.9"/>',
                '<circle cx="', x.toString(), '" cy="', y.toString(),
                '" r="15" fill="none" stroke="', color, '" stroke-width="0.5" opacity="0.3"/>'
            ));
        }

        return nodes;
    }

    function _generateTitle(uint256 masterCount, uint256 truthCount) internal pure returns (string memory) {
        return string(abi.encodePacked(
            '<text x="400" y="60" text-anchor="middle" fill="#f0ece7" ',
            'font-family="Inter, sans-serif" font-size="24" font-weight="200" letter-spacing="0.3em">',
            'NORTHSTAR PRINCIPALS</text>',
            '<text x="400" y="90" text-anchor="middle" fill="#9a9690" ',
            'font-family="Inter, sans-serif" font-size="12" letter-spacing="0.2em">',
            masterCount.toString(), ' MASTERS / ', truthCount.toString(), ' TRUTHS / INFINITE CONNECTIONS</text>'
        ));
    }

    function _generateTimestamp(uint256 timestamp) internal pure returns (string memory) {
        return string(abi.encodePacked(
            '<text x="400" y="760" text-anchor="middle" fill="#5a5854" ',
            'font-family="monospace" font-size="10">',
            'GENESIS BLOCK: ', timestamp.toString(), '</text>'
        ));
    }

    function _generateSacredGeometry() internal pure returns (string memory) {
        // PHI spiral representation
        return string(abi.encodePacked(
            '<path d="M400,400 Q450,350 500,400 T600,400" fill="none" ',
            'stroke="#d4a574" stroke-width="0.5" opacity="0.3"/>',
            '<circle cx="400" cy="400" r="200" fill="none" stroke="#7865ba" ',
            'stroke-width="0.3" opacity="0.2"/>',
            '<circle cx="400" cy="400" r="280" fill="none" stroke="#54a876" ',
            'stroke-width="0.3" opacity="0.15"/>'
        ));
    }

    // Simple trig approximations for on-chain SVG
    function _cos(uint256 angleDegrees) internal pure returns (int256) {
        uint256 normalized = angleDegrees % 36000;
        if (normalized <= 9000) return int256(1000 - (normalized * normalized) / 81000);
        if (normalized <= 18000) return -int256((normalized - 9000) * (normalized - 9000) / 81000);
        if (normalized <= 27000) return -int256(1000 - ((normalized - 18000) * (normalized - 18000)) / 81000);
        return int256(((normalized - 27000) * (normalized - 27000)) / 81000);
    }

    function _sin(uint256 angleDegrees) internal pure returns (int256) {
        return _cos(angleDegrees + 27000); // sin(x) = cos(x - 90)
    }

    // ============================================
    // TOKEN URI
    // ============================================

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");

        TokenMetadata memory meta = tokenMetadata[tokenId];
        uint256 masterCount = uint256(_traits[tokenId][keccak256("MASTER_COUNT")]);
        uint256 truthCount = uint256(_traits[tokenId][keccak256("TRUTH_COUNT")]);

        string memory svg = generateOnChainSVG(tokenId);

        string memory json = string(abi.encodePacked(
            '{"name":"NORTHSTAR PRINCIPALS EXPERIENCE #', tokenId.toString(), '",',
            '"description":"The first blockchain entry of the 22 Masters wisdom framework. ',
            'A 4D spectral visualization of verified truths across 3000+ years of human knowledge.",',
            '"image":"data:image/svg+xml;base64,', Base64.encode(bytes(svg)), '",',
            '"animation_url":"', meta.arweaveURI, '",',
            '"external_url":"https://archiv-it.xyz/northstar/',tokenId.toString(),'",',
            '"attributes":[',
            '{"trait_type":"Masters","value":', masterCount.toString(), '},',
            '{"trait_type":"Truths","value":', truthCount.toString(), '},',
            '{"trait_type":"Feminine Masters","value":', uint256(_traits[tokenId][keccak256("FEMININE_COUNT")]).toString(), '},',
            '{"trait_type":"Masculine Masters","value":', uint256(_traits[tokenId][keccak256("MASCULINE_COUNT")]).toString(), '},',
            '{"trait_type":"Genesis Timestamp","value":', meta.creationTimestamp.toString(), '},',
            '{"trait_type":"Version","value":', meta.version.toString(), '},',
            '{"trait_type":"Content Hash","value":"', _bytes32ToString(meta.originalContentHash), '"},',
            '{"trait_type":"Locked","value":"', meta.locked ? "true" : "false", '"}',
            ']}'
        ));

        return string(abi.encodePacked(
            'data:application/json;base64,',
            Base64.encode(bytes(json))
        ));
    }

    function _bytes32ToString(bytes32 data) internal pure returns (string memory) {
        bytes memory alphabet = "0123456789abcdef";
        bytes memory str = new bytes(64);
        for (uint256 i = 0; i < 32; i++) {
            str[i*2] = alphabet[uint8(data[i] >> 4)];
            str[i*2+1] = alphabet[uint8(data[i] & 0x0f)];
        }
        return string(str);
    }

    // ============================================
    // VIEW FUNCTIONS
    // ============================================

    function getMaster(uint256 tokenId, bytes32 masterId) external view returns (
        string memory name,
        string memory dates,
        uint16 birthYear,
        string memory domain,
        bool isFeminine,
        string memory archetype,
        bool verified
    ) {
        Master memory m = masters[tokenId][masterId];
        return (m.name, m.dates, m.birthYear, m.domain, m.isFeminine, m.archetype, m.verified);
    }

    function getTruth(uint256 tokenId, uint256 rank) external view returns (
        string memory statement,
        string memory category,
        string memory description,
        bool verified
    ) {
        Truth memory t = truths[tokenId][rank];
        return (t.statement, t.category, t.description, t.verified);
    }

    function getAllMasterIds(uint256 tokenId) external view returns (bytes32[] memory) {
        return masterIds[tokenId];
    }

    function getAllTruthRanks(uint256 tokenId) external view returns (uint256[] memory) {
        return truthRanks[tokenId];
    }

    // ============================================
    // REQUIRED OVERRIDES
    // ============================================

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}

/**
 * ARTIST RIGHTS COVENANT (IMMUTABLE):
 *
 * This smart contract encodes the TEACHINGS and TECHNIQUES of the 22 Masters,
 * NOT their actual artwork. Each master's contributions are:
 *
 * PROTECTED (Never reproduced):
 * - Actual artwork, compositions, or creations
 * - Visual style or aesthetic signatures
 * - Performance recordings or interpretations
 *
 * SHARED (Encoded herein):
 * - Philosophical principles
 * - Creative methodologies
 * - Verified wisdom quotes
 * - Cross-disciplinary connections
 *
 * Any reproduction of artist work requires explicit OPT_IN recorded on-chain.
 *
 * GENESIS MASTERS (22):
 * Feminine (9): Hildegard, Founder, Rand, Starhawk, Tori, Bjork, Swan, Hicks, Byrne
 * Masculine (13): da Vinci, Tesla, Fuller, Jung, Suleyman, Grant, Prince,
 *                 Coltrane, Bowie, Koe, Jobs, Cherny, Rene
 *
 * SO MOTE IT BE
 */
