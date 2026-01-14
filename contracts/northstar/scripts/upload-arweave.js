#!/usr/bin/env node
/**
 * NORTHSTAR PRINCIPALS - Direct Arweave Upload
 * =============================================
 *
 * Uploads directly to the Arweave network using the official arweave-js library.
 * No middleman services. Pure decentralized permanent storage.
 *
 * Prerequisites:
 * 1. Arweave wallet JSON file (get from https://arweave.app/wallet)
 * 2. AR tokens in wallet (get from exchange or https://faucet.arweave.net for testnet)
 *
 * Usage:
 *   node scripts/upload-arweave.js --wallet /path/to/arweave-wallet.json
 */

const Arweave = require('arweave');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Initialize Arweave
const arweave = Arweave.init({
  host: 'arweave.net',
  port: 443,
  protocol: 'https',
  timeout: 60000,
  logging: false
});

// File to upload
const VISUALIZATION_PATH = path.resolve(__dirname, '../../../scripts/interface/templates/masters_point_cloud_v3_spectral.html');

async function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║     NORTHSTAR PRINCIPALS - DIRECT ARWEAVE UPLOAD               ║
║              No middlemen. Pure decentralization.              ║
╚════════════════════════════════════════════════════════════════╝
`);

  // Parse command line args
  const args = process.argv.slice(2);
  const walletIndex = args.indexOf('--wallet');

  if (walletIndex === -1 || !args[walletIndex + 1]) {
    console.log(`
Usage: node scripts/upload-arweave.js --wallet /path/to/arweave-wallet.json

To get an Arweave wallet:
1. Go to https://arweave.app/wallet
2. Click "Create Wallet"
3. Download the JSON keyfile
4. Fund it with AR tokens

To get AR tokens:
- Testnet: https://faucet.arweave.net (free, for testing)
- Mainnet: Buy AR on exchanges (Binance, Crypto.com, etc.)
           Or use https://arweave.app to convert ETH → AR

Estimated cost: ~0.001 AR (~$0.02) for 68KB file
`);
    process.exit(1);
  }

  const walletPath = args[walletIndex + 1];

  // Check wallet file exists
  if (!fs.existsSync(walletPath)) {
    console.error(`Wallet file not found: ${walletPath}`);
    process.exit(1);
  }

  // Check visualization file exists
  if (!fs.existsSync(VISUALIZATION_PATH)) {
    console.error(`Visualization file not found: ${VISUALIZATION_PATH}`);
    process.exit(1);
  }

  // Load wallet
  console.log('Loading Arweave wallet...');
  const walletData = JSON.parse(fs.readFileSync(walletPath, 'utf8'));

  // Get wallet address and balance
  const address = await arweave.wallets.jwkToAddress(walletData);
  const balance = await arweave.wallets.getBalance(address);
  const arBalance = arweave.ar.winstonToAr(balance);

  console.log(`Wallet Address: ${address}`);
  console.log(`Balance: ${arBalance} AR`);
  console.log('');

  // Load file
  console.log('Loading visualization file...');
  const fileData = fs.readFileSync(VISUALIZATION_PATH);
  const fileSize = fileData.length;

  console.log(`File: masters_point_cloud_v3_spectral.html`);
  console.log(`Size: ${(fileSize / 1024).toFixed(2)} KB`);

  // Calculate content hash
  const contentHash = '0x' + crypto.createHash('sha256').update(fileData).digest('hex');
  console.log(`SHA256: ${contentHash}`);
  console.log('');

  // Estimate cost
  const cost = await arweave.transactions.getPrice(fileSize);
  const costAr = arweave.ar.winstonToAr(cost);
  console.log(`Estimated Cost: ${costAr} AR`);

  if (parseFloat(arBalance) < parseFloat(costAr)) {
    console.error(`
Insufficient balance!
Required: ${costAr} AR
Available: ${arBalance} AR

Fund your wallet at: https://arweave.app
Or get testnet tokens: https://faucet.arweave.net
`);
    process.exit(1);
  }

  console.log('');
  console.log('Creating transaction...');

  // Create transaction
  const transaction = await arweave.createTransaction({
    data: fileData
  }, walletData);

  // Add tags for discoverability
  transaction.addTag('Content-Type', 'text/html');
  transaction.addTag('App-Name', 'NORTHSTAR-PRINCIPALS');
  transaction.addTag('App-Version', '1.0.0');
  transaction.addTag('Type', '4D-Spectral-Visualization');
  transaction.addTag('Masters-Count', '22');
  transaction.addTag('Truths-Count', '100');
  transaction.addTag('Content-Hash', contentHash);
  transaction.addTag('Created-By', 'ARCHIV-IT');
  transaction.addTag('Description', 'NORTHSTAR PRINCIPALS EXPERIENCE - 22 Masters / 100 Truths / Infinite Connections');

  console.log(`Transaction ID: ${transaction.id}`);
  console.log('');

  // Sign transaction
  console.log('Signing transaction...');
  await arweave.transactions.sign(transaction, walletData);

  // Verify signature
  const verified = await arweave.transactions.verify(transaction);
  if (!verified) {
    console.error('Transaction signature verification failed!');
    process.exit(1);
  }
  console.log('Signature verified ✓');
  console.log('');

  // Submit transaction
  console.log('Submitting to Arweave network...');
  console.log('(This may take a moment...)');
  console.log('');

  const response = await arweave.transactions.post(transaction);

  if (response.status === 200 || response.status === 202) {
    const arweaveUri = `ar://${transaction.id}`;
    const gatewayUrl = `https://arweave.net/${transaction.id}`;

    console.log(`
═══════════════════════════════════════════════════════════════
                    UPLOAD SUCCESSFUL!
═══════════════════════════════════════════════════════════════

Transaction ID: ${transaction.id}

Arweave URI (use this for NFT):
  ${arweaveUri}

Gateway URL (view in browser):
  ${gatewayUrl}

Status: ${response.status === 200 ? 'Confirmed' : 'Pending confirmation'}

Note: It may take 5-15 minutes for the transaction to be
      confirmed and the file to be accessible via gateways.

═══════════════════════════════════════════════════════════════
`);

    // Save upload info
    const uploadInfo = {
      transactionId: transaction.id,
      arweaveUri: arweaveUri,
      gatewayUrl: gatewayUrl,
      contentHash: contentHash,
      fileSize: fileSize,
      cost: costAr,
      timestamp: new Date().toISOString(),
      walletAddress: address,
      status: response.status === 200 ? 'confirmed' : 'pending'
    };

    fs.writeFileSync(
      path.join(__dirname, '../arweave-upload.json'),
      JSON.stringify(uploadInfo, null, 2)
    );

    console.log('Upload info saved to: contracts/northstar/arweave-upload.json');
    console.log('');
    console.log('Next step: Use this Arweave URI when minting:');
    console.log(`  ARWEAVE_URI="${arweaveUri}" npx hardhat run scripts/mint.js --network mainnet`);

  } else {
    console.error(`Upload failed with status: ${response.status}`);
    console.error(response.data);
    process.exit(1);
  }
}

// Check transaction status
async function checkStatus(txId) {
  try {
    const status = await arweave.transactions.getStatus(txId);
    return status;
  } catch (e) {
    return { status: 'pending' };
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
