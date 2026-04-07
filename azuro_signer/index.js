const express = require('express');
const { ethers } = require('ethers');
const cors = require('cors');
const { getBetTypedData } = require('@azuro-org/toolkit');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3000;

app.post('/sign', async (req, res) => {
    try {
        const { privateKey, clientData, bet } = req.body;
        
        if (!privateKey || !clientData || !bet) {
            return res.status(400).json({ error: 'Missing required parameters: privateKey, clientData, bet' });
        }

        const wallet = new ethers.Wallet(privateKey);
        
        // Ensure values are BigInt/numbers where required by Azuro toolkit
        clientData.expiresAt = BigInt(clientData.expiresAt);
        clientData.chainId = BigInt(clientData.chainId);
        clientData.relayerFeeAmount = BigInt(clientData.relayerFeeAmount || 0);
        
        // Pass boolean or defaults
        clientData.isBetSponsored = clientData.isBetSponsored || false;
        clientData.isFeeSponsored = clientData.isFeeSponsored || false;
        clientData.isSponsoredBetReturnable = clientData.isSponsoredBetReturnable || false;

        bet.conditionId = BigInt(bet.conditionId);
        bet.outcomeId = BigInt(bet.outcomeId);
        bet.minOdds = BigInt(bet.minOdds);
        bet.amount = BigInt(bet.amount);
        bet.nonce = BigInt(bet.nonce || Date.now());

        // Use official Toolkit to generate 100% correct type data structures 
        // This resolves the Relayer/BetaData/Express messageNotVerified differences
        const typedData = getBetTypedData({
            account: wallet.address,
            clientData: clientData,
            bet: bet
        });
        
        // We delete account since ethers.js doesn't need it. We just pass domain, types, message
        const { domain, types, message } = typedData;

        // Ethers v6 handles signing typed data natively
        const signature = await wallet.signTypedData(domain, types, message);
        
        return res.json({ signature });

    } catch (error) {
        console.error("Signing error:", error.stack);
        return res.status(500).json({ error: error.message, stack: error.stack });
    }
});

app.listen(PORT, () => {
    console.log(`Azuro Official SDK Signer microservice listening on port ${PORT}`);
});
