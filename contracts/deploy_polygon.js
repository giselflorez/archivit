/**
 * ARCHIV-IT ACCUMETER NFT - Polygon Deployment Script
 *
 * This script deploys the ArchivitAccumeter ERC-721 contract to Polygon network.
 *
 * Prerequisites:
 * 1. Install dependencies: npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox @openzeppelin/contracts dotenv
 * 2. Create .env file with:
 *    - POLYGON_RPC_URL (e.g., https://polygon-rpc.com or Alchemy/Infura endpoint)
 *    - PRIVATE_KEY (deployer wallet private key - DO NOT commit this!)
 *    - POLYGONSCAN_API_KEY (for contract verification)
 * 3. Ensure deployer wallet has MATIC for gas
 *
 * Usage:
 *   npx hardhat run scripts/deploy_polygon.js --network polygon
 *
 * For testnet (Mumbai):
 *   npx hardhat run scripts/deploy_polygon.js --network mumbai
 */

const { ethers, run, network } = require("hardhat");

async function main() {
    console.log("=".repeat(60));
    console.log("ARCHIV-IT ACCUMETER NFT - Deployment Script");
    console.log("=".repeat(60));
    console.log("");

    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    const deployerAddress = await deployer.getAddress();

    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Deployer:", deployerAddress);
    console.log("");

    // Check deployer balance
    const balance = await ethers.provider.getBalance(deployerAddress);
    const balanceInMatic = ethers.formatEther(balance);
    console.log(`Deployer balance: ${balanceInMatic} MATIC`);

    if (parseFloat(balanceInMatic) < 0.1) {
        console.warn("WARNING: Low balance. Ensure you have enough MATIC for deployment.");
    }
    console.log("");

    // Deploy the contract
    console.log("Deploying ArchivitAccumeter contract...");
    console.log("");

    const ArchivitAccumeter = await ethers.getContractFactory("ArchivitAccumeter");

    // Constructor takes the initial owner address
    const contract = await ArchivitAccumeter.deploy(deployerAddress);

    await contract.waitForDeployment();

    const contractAddress = await contract.getAddress();

    console.log("-".repeat(60));
    console.log("DEPLOYMENT SUCCESSFUL");
    console.log("-".repeat(60));
    console.log("");
    console.log("Contract Address:", contractAddress);
    console.log("Owner:", deployerAddress);
    console.log("");

    // Get deployment transaction details
    const deploymentTx = contract.deploymentTransaction();
    if (deploymentTx) {
        console.log("Transaction Hash:", deploymentTx.hash);
        console.log("Block Number:", deploymentTx.blockNumber);
        console.log("");
    }

    // Verify contract on Polygonscan (skip for local networks)
    if (network.name !== "hardhat" && network.name !== "localhost") {
        console.log("Waiting for block confirmations before verification...");
        // Wait for 6 block confirmations
        await deploymentTx.wait(6);

        console.log("Verifying contract on Polygonscan...");
        try {
            await run("verify:verify", {
                address: contractAddress,
                constructorArguments: [deployerAddress],
            });
            console.log("Contract verified successfully!");
        } catch (error) {
            if (error.message.includes("Already Verified")) {
                console.log("Contract is already verified.");
            } else {
                console.error("Verification failed:", error.message);
                console.log("You can verify manually later with:");
                console.log(`npx hardhat verify --network ${network.name} ${contractAddress} ${deployerAddress}`);
            }
        }
    }

    console.log("");
    console.log("=".repeat(60));
    console.log("NEXT STEPS");
    console.log("=".repeat(60));
    console.log("");
    console.log("1. Update badge_nft_system.py with the contract address:");
    console.log(`   'polygon': { 'contract': '${contractAddress}', ... }`);
    console.log("");
    console.log("2. Test the contract:");
    console.log("   - Mint a test NFT with a userHash");
    console.log("   - Verify tokenURI returns expected metadata endpoint");
    console.log("   - Test verifyOwnership function");
    console.log("");
    console.log("3. View on Polygonscan:");
    if (network.name === "mumbai") {
        console.log(`   https://mumbai.polygonscan.com/address/${contractAddress}`);
    } else {
        console.log(`   https://polygonscan.com/address/${contractAddress}`);
    }
    console.log("");

    // Return deployment info for testing
    return {
        contract: contractAddress,
        owner: deployerAddress,
        network: network.name,
        chainId: network.config.chainId
    };
}

// Export for testing
module.exports = { main };

// Run deployment
main()
    .then((result) => {
        console.log("Deployment complete!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
