// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title ArchivitAccumeter
 * @dev ARCHIV-IT ACU-METER NFT - Dynamic data consistency indicator
 *
 * This ERC-721 token represents a user's ARCHIV-IT identity and serves as
 * a dynamic badge that reflects their data consistency score. The tokenURI
 * points to a server endpoint that returns real-time metadata based on
 * the current trust score.
 *
 * Security Model (Dual Verification):
 * - NFT ownership proves wallet control (on-chain)
 * - Server registration links NFT to ARCHIV-IT user (off-chain)
 * - Both must match for valid badge access
 *
 * One NFT per userHash enforced to prevent duplicate registrations.
 */
contract ArchivitAccumeter is ERC721, Ownable {
    using Strings for uint256;

    // Base URI for token metadata (dynamic endpoint)
    string private _baseTokenURI;

    // Token ID counter (starts at 1)
    uint256 private _tokenIdCounter;

    // Mapping from token ID to ARCHIV-IT user hash
    // userHash = keccak256(userId) computed off-chain
    mapping(uint256 => bytes32) public tokenUserHashes;

    // Mapping from user hash to token ID (enforces one NFT per user)
    // A value of 0 means no token exists for this user
    mapping(bytes32 => uint256) public userHashToTokenId;

    // Events
    event AccumeterMinted(
        address indexed owner,
        uint256 indexed tokenId,
        bytes32 indexed userHash
    );

    event BaseURIUpdated(string oldURI, string newURI);

    // Errors
    error AccumeterAlreadyMinted(bytes32 userHash);
    error InvalidUserHash();
    error TokenDoesNotExist(uint256 tokenId);

    /**
     * @dev Constructor sets name, symbol, owner, and base URI
     * @param initialOwner Address that will own the contract
     */
    constructor(address initialOwner)
        ERC721("ARCHIV-IT ACCUMETER", "ACCUM")
        Ownable(initialOwner)
    {
        _baseTokenURI = "https://archivit.web3photo.com/api/nft/metadata/";
    }

    /**
     * @dev Mint a new ACCUMETER NFT
     * @param userHash keccak256 hash of the ARCHIV-IT user ID
     * @return tokenId The newly minted token ID
     *
     * Requirements:
     * - userHash must not be empty (zero bytes32)
     * - userHash must not already have a minted token
     *
     * Note: Anyone can mint, but the userHash links to their ARCHIV-IT account.
     * The server-side verification ensures only the correct user benefits.
     */
    function mint(bytes32 userHash) external returns (uint256) {
        // Validate userHash is not empty
        if (userHash == bytes32(0)) {
            revert InvalidUserHash();
        }

        // Check if user already has an ACCUMETER
        if (userHashToTokenId[userHash] != 0) {
            revert AccumeterAlreadyMinted(userHash);
        }

        // Increment counter and mint
        _tokenIdCounter++;
        uint256 newTokenId = _tokenIdCounter;

        _safeMint(msg.sender, newTokenId);

        // Store mappings
        tokenUserHashes[newTokenId] = userHash;
        userHashToTokenId[userHash] = newTokenId;

        emit AccumeterMinted(msg.sender, newTokenId, userHash);

        return newTokenId;
    }

    /**
     * @dev Returns the token URI for a given token ID
     * @param tokenId The token ID to query
     * @return The full URI string pointing to the metadata endpoint
     *
     * The metadata endpoint returns dynamic data based on current trust score:
     * {
     *   "name": "ACCUMETER #1",
     *   "description": "Dynamic data consistency indicator...",
     *   "image": "https://archivit.web3photo.com/badge/{userId}/nft.svg",
     *   "attributes": [{ "trait_type": "Trust Score", "value": 85 }, ...]
     * }
     */
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        if (_ownerOf(tokenId) == address(0)) {
            revert TokenDoesNotExist(tokenId);
        }
        return string(abi.encodePacked(_baseTokenURI, tokenId.toString()));
    }

    /**
     * @dev Verify that a wallet owns the ACCUMETER for a specific user
     * @param userHash keccak256 hash of the ARCHIV-IT user ID
     * @param wallet Address to check ownership
     * @return bool True if wallet owns the ACCUMETER for this userHash
     *
     * This function is called by the ARCHIV-IT server to verify on-chain
     * ownership before returning badge data.
     */
    function verifyOwnership(bytes32 userHash, address wallet) external view returns (bool) {
        uint256 tokenId = userHashToTokenId[userHash];

        // No token minted for this user
        if (tokenId == 0) {
            return false;
        }

        // Check if wallet is the current owner
        return ownerOf(tokenId) == wallet;
    }

    /**
     * @dev Get the token ID for a user hash
     * @param userHash keccak256 hash of the ARCHIV-IT user ID
     * @return tokenId The token ID (0 if no token exists)
     */
    function getTokenForUser(bytes32 userHash) external view returns (uint256) {
        return userHashToTokenId[userHash];
    }

    /**
     * @dev Get the user hash for a token ID
     * @param tokenId The token ID to query
     * @return userHash The associated user hash
     */
    function getUserHashForToken(uint256 tokenId) external view returns (bytes32) {
        if (_ownerOf(tokenId) == address(0)) {
            revert TokenDoesNotExist(tokenId);
        }
        return tokenUserHashes[tokenId];
    }

    /**
     * @dev Update the base URI for token metadata
     * @param newBaseURI The new base URI
     *
     * Only callable by contract owner. Use this if the metadata
     * endpoint URL changes.
     */
    function setBaseURI(string memory newBaseURI) external onlyOwner {
        string memory oldURI = _baseTokenURI;
        _baseTokenURI = newBaseURI;
        emit BaseURIUpdated(oldURI, newBaseURI);
    }

    /**
     * @dev Get the current base URI
     * @return The current base URI string
     */
    function getBaseURI() external view returns (string memory) {
        return _baseTokenURI;
    }

    /**
     * @dev Get the total number of tokens minted
     * @return Total supply count
     */
    function totalSupply() external view returns (uint256) {
        return _tokenIdCounter;
    }

    /**
     * @dev Check if a user hash already has a minted token
     * @param userHash The user hash to check
     * @return bool True if an ACCUMETER exists for this user
     */
    function hasMinted(bytes32 userHash) external view returns (bool) {
        return userHashToTokenId[userHash] != 0;
    }
}
