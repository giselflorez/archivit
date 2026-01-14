#!/usr/bin/env node
/**
 * NORTHSTAR PRINCIPALS - Pinata IPFS Upload
 * ==========================================
 *
 * Uploads to IPFS via Pinata as redundant backup storage.
 * Get your API keys at: https://app.pinata.cloud/keys
 *
 * Usage:
 *   PINATA_API_KEY=xxx PINATA_SECRET=yyy node scripts/upload-pinata.js
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');

// File to upload
const VISUALIZATION_PATH = path.resolve(__dirname, '../../../scripts/interface/templates/masters_point_cloud_v3_spectral.html');

async function uploadToPinata(apiKey, secretKey, fileData, fileName) {
  return new Promise((resolve, reject) => {
    const boundary = '----FormBoundary' + crypto.randomBytes(16).toString('hex');

    const header = [
      `--${boundary}`,
      `Content-Disposition: form-data; name="file"; filename="${fileName}"`,
      'Content-Type: text/html',
      '',
      ''
    ].join('\r\n');

    const footer = `\r\n--${boundary}--\r\n`;

    const metadata = JSON.stringify({
      name: 'NORTHSTAR_PRINCIPALS_EXPERIENCE_v3',
      keyvalues: {
        app: 'NORTHSTAR-PRINCIPALS',
        type: '4D-Spectral-Visualization',
        masters: '22',
        truths: '100',
        created_by: 'ARCHIV-IT'
      }
    });

    const metadataPart = [
      `--${boundary}`,
      'Content-Disposition: form-data; name="pinataMetadata"',
      'Content-Type: application/json',
      '',
      metadata,
      ''
    ].join('\r\n');

    const body = Buffer.concat([
      Buffer.from(header),
      fileData,
      Buffer.from('\r\n' + metadataPart + footer)
    ]);

    const options = {
      hostname: 'api.pinata.cloud',
      port: 443,
      path: '/pinning/pinFileToIPFS',
      method: 'POST',
      headers: {
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': body.length,
        'pinata_api_key': apiKey,
        'pinata_secret_api_key': secretKey
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`Pinata error ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║     NORTHSTAR PRINCIPALS - PINATA IPFS UPLOAD                  ║
║              Redundant backup on IPFS                          ║
╚════════════════════════════════════════════════════════════════╝
`);

  const apiKey = process.env.PINATA_API_KEY;
  const secretKey = process.env.PINATA_SECRET;

  if (!apiKey || !secretKey) {
    console.log(`
Usage: PINATA_API_KEY=xxx PINATA_SECRET=yyy node scripts/upload-pinata.js

To get Pinata API keys:
1. Go to https://app.pinata.cloud/keys
2. Click "New Key"
3. Enable "pinFileToIPFS" permission
4. Copy the API Key and Secret

Free tier includes 500MB storage.
`);
    process.exit(1);
  }

  // Check visualization file exists
  if (!fs.existsSync(VISUALIZATION_PATH)) {
    console.error(`Visualization file not found: ${VISUALIZATION_PATH}`);
    process.exit(1);
  }

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

  console.log('Uploading to Pinata...');
  console.log('');

  try {
    const result = await uploadToPinata(
      apiKey,
      secretKey,
      fileData,
      'masters_point_cloud_v3_spectral.html'
    );

    const ipfsUri = `ipfs://${result.IpfsHash}`;
    const gatewayUrl = `https://gateway.pinata.cloud/ipfs/${result.IpfsHash}`;

    console.log(`
═══════════════════════════════════════════════════════════════
                    UPLOAD SUCCESSFUL!
═══════════════════════════════════════════════════════════════

IPFS Hash: ${result.IpfsHash}

IPFS URI (use this for NFT backup):
  ${ipfsUri}

Gateway URL (view in browser):
  ${gatewayUrl}

Pin Size: ${result.PinSize} bytes

═══════════════════════════════════════════════════════════════
`);

    // Save upload info
    const uploadInfo = {
      ipfsHash: result.IpfsHash,
      ipfsUri: ipfsUri,
      gatewayUrl: gatewayUrl,
      contentHash: contentHash,
      fileSize: fileSize,
      pinSize: result.PinSize,
      timestamp: new Date().toISOString()
    };

    fs.writeFileSync(
      path.join(__dirname, '../pinata-upload.json'),
      JSON.stringify(uploadInfo, null, 2)
    );

    console.log('Upload info saved to: contracts/northstar/pinata-upload.json');
    console.log('');
    console.log('Use this IPFS URI as backup when minting:');
    console.log(`  IPFS_URI="${ipfsUri}"`);

  } catch (error) {
    console.error('Upload failed:', error.message);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
