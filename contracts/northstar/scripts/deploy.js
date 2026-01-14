const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║     NORTHSTAR PRINCIPALS EXPERIENCE - DEPLOYING TO CHAIN       ║
╚════════════════════════════════════════════════════════════════╝
  `);

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "ETH");
  console.log("");

  // Load content hashes
  const hashes = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../content_hashes.json"),
    "utf8"
  ));

  console.log("Content Hash:", hashes.sha256);
  console.log("Visualization Hash:", hashes.keccak256);
  console.log("");

  // Deploy the contract
  console.log("Deploying NorthstarPrincipals...");

  const NorthstarPrincipals = await hre.ethers.getContractFactory("NorthstarPrincipals");

  // Constructor args: founder address, array of verifier addresses
  const verifiers = []; // Add verifier addresses here if needed

  const contract = await NorthstarPrincipals.deploy(
    deployer.address,  // founder
    verifiers          // verifiers array
  );

  await contract.waitForDeployment();

  const contractAddress = await contract.getAddress();

  console.log("");
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("CONTRACT DEPLOYED!");
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("Address:", contractAddress);
  console.log("Network:", hre.network.name);
  console.log("");

  // Save deployment info
  const deploymentInfo = {
    contractAddress,
    network: hre.network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contentHash: hashes.sha256,
    visualizationHash: hashes.keccak256,
    transactionHash: contract.deploymentTransaction()?.hash
  };

  fs.writeFileSync(
    path.join(__dirname, "../deployment.json"),
    JSON.stringify(deploymentInfo, indent=2)
  );

  console.log("Deployment info saved to deployment.json");
  console.log("");
  console.log("NEXT STEP: Run mint script with Arweave and IPFS URIs");
  console.log("  npx hardhat run scripts/mint.js --network", hre.network.name);
  console.log("");

  // Verify on Etherscan if not on localhost
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("Verifying on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: [deployer.address, verifiers]
      });
      console.log("Contract verified!");
    } catch (e) {
      console.log("Verification failed:", e.message);
      console.log("You can verify manually later with:");
      console.log(`  npx hardhat verify --network ${hre.network.name} ${contractAddress} ${deployer.address} "[]"`);
    }
  }

  console.log(`
═══════════════════════════════════════════════════════════════
                    DEPLOYMENT COMPLETE
═══════════════════════════════════════════════════════════════
  `);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
