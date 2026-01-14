const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

// ═══════════════════════════════════════════════════════════════
// CONFIGURE THESE BEFORE RUNNING
// ═══════════════════════════════════════════════════════════════

const ARWEAVE_URI = process.env.ARWEAVE_URI || "ar://YOUR_ARWEAVE_TX_ID";
const IPFS_URI = process.env.IPFS_URI || "ipfs://YOUR_IPFS_CID";

// ═══════════════════════════════════════════════════════════════

async function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║     NORTHSTAR PRINCIPALS EXPERIENCE - MINTING GENESIS          ║
╚════════════════════════════════════════════════════════════════╝
  `);

  // Load deployment info
  const deploymentPath = path.join(__dirname, "../deployment.json");
  if (!fs.existsSync(deploymentPath)) {
    console.error("deployment.json not found! Run deploy.js first.");
    process.exit(1);
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  const hashes = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../content_hashes.json"),
    "utf8"
  ));

  console.log("Contract Address:", deployment.contractAddress);
  console.log("Content Hash:", hashes.sha256);
  console.log("Arweave URI:", ARWEAVE_URI);
  console.log("IPFS URI:", IPFS_URI);
  console.log("");

  if (ARWEAVE_URI === "ar://YOUR_ARWEAVE_TX_ID") {
    console.error("⚠️  Please set ARWEAVE_URI before minting!");
    console.log("");
    console.log("1. Upload to Arweave first:");
    console.log("   - Go to https://irys.xyz or https://app.ardrive.io");
    console.log("   - Upload: scripts/interface/templates/masters_point_cloud_v3_spectral.html");
    console.log("   - Get the ar:// URI");
    console.log("");
    console.log("2. Then run with:");
    console.log(`   ARWEAVE_URI="ar://xxx" IPFS_URI="ipfs://xxx" npx hardhat run scripts/mint.js --network ${hre.network.name}`);
    process.exit(1);
  }

  const [signer] = await hre.ethers.getSigners();
  console.log("Minting from:", signer.address);

  // Get contract instance
  const contract = await hre.ethers.getContractAt(
    "NorthstarPrincipals",
    deployment.contractAddress,
    signer
  );

  console.log("");
  console.log("Calling mintGenesis...");

  const tx = await contract.mintGenesis(
    hashes.sha256,
    hashes.keccak256,
    ARWEAVE_URI,
    IPFS_URI
  );

  console.log("Transaction sent:", tx.hash);
  console.log("Waiting for confirmation...");

  const receipt = await tx.wait();

  console.log("");
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("🌟 GENESIS NORTHSTAR MINTED! 🌟");
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("Token ID: 0 (Genesis)");
  console.log("Transaction:", receipt.hash);
  console.log("Block:", receipt.blockNumber);
  console.log("Gas Used:", receipt.gasUsed.toString());
  console.log("");

  // Update deployment info
  deployment.genesisMinted = true;
  deployment.genesisTransaction = receipt.hash;
  deployment.genesisBlock = receipt.blockNumber;
  deployment.arweaveURI = ARWEAVE_URI;
  deployment.ipfsURI = IPFS_URI;

  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));

  // Get token URI
  const tokenURI = await contract.tokenURI(0);
  console.log("Token URI (on-chain):");
  console.log(tokenURI.slice(0, 200) + "...");
  console.log("");

  console.log(`
═══════════════════════════════════════════════════════════════
               THE NORTHSTAR IS NOW ON CHAIN
═══════════════════════════════════════════════════════════════

22 Masters encoded forever:
  Feminine (9): Hildegard, Gisel, Rand, Starhawk, Tori,
                Bjork, Swan, Hicks, Byrne
  Masculine (13): da Vinci, Tesla, Fuller, Jung, Suleyman,
                  Grant, Prince, Coltrane, Bowie, Koe,
                  Jobs, Cherny, Rene

View on:
  - Etherscan: https://etherscan.io/token/${deployment.contractAddress}
  - OpenSea: https://opensea.io/assets/ethereum/${deployment.contractAddress}/0

NEXT: Create Token Bound Account (ERC-6551)
  npx hardhat run scripts/create-tba.js --network ${hre.network.name}

SO MOTE IT BE
═══════════════════════════════════════════════════════════════
  `);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
