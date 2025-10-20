# How to Get Redpanda Connection Details

## Your Redpanda Cluster
- **Name:** corch-facilitair-redpanda
- **ID:** d3palehmqts75cf5bu50

---

## Step 1: Access Redpanda Cloud Console

Go to: https://cloud.redpanda.com/

---

## Step 2: Select Your Cluster

1. Click on **"corch-facilitair-redpanda"** cluster
2. Or find cluster ID: **d3palehmqts75cf5bu50**

---

## Step 3: Get Connection Details

### Option A: Via "Overview" Tab

1. Click **"Overview"** in left sidebar
2. Look for **"Bootstrap servers"** or **"Kafka API"** section
3. Copy the broker address (looks like: `seed-abc123.cloud.redpanda.com:9092`)

### Option B: Via "Security" Tab

1. Click **"Security"** in left sidebar
2. Click **"SASL/SCRAM"**
3. Create a user if you haven't (or use existing)
4. Note the username and password

### Option C: Via "Connect" Button

1. Look for **"Connect"** or **"How to Connect"** button
2. Select **"Kafka clients"**
3. Copy the connection string

---

## What You're Looking For

You need these 4 values:

```bash
REDPANDA_BROKER=seed-XXXXXXX.cloud.redpanda.com:9092
REDPANDA_USERNAME=your-username
REDPANDA_PASSWORD=your-password
REDPANDA_SASL_MECHANISM=SCRAM-SHA-256
```

---

## Typical Locations in Redpanda UI

### Location 1: Cluster Overview Page
```
Redpanda Cloud Console
└── Clusters
    └── corch-facilitair-redpanda
        └── Overview
            └── Connection Details
                ├── Bootstrap Servers: seed-xyz.cloud.redpanda.com:9092
                └── Authentication: SASL/SCRAM
```

### Location 2: Security/SASL Tab
```
Redpanda Cloud Console
└── Clusters
    └── corch-facilitair-redpanda
        └── Security
            └── SASL/SCRAM
                └── Create User
                    ├── Username: (you choose)
                    └── Password: (generated)
```

---

## Quick Test Once You Have Details

```bash
# Test connection with rpk CLI (if installed)
rpk cluster info \
  --brokers $REDPANDA_BROKER \
  --user $REDPANDA_USERNAME \
  --password $REDPANDA_PASSWORD \
  --sasl-mechanism SCRAM-SHA-256

# Or test with Python
python3 -c "
from kafka import KafkaProducer
producer = KafkaProducer(
    bootstrap_servers='YOUR_BROKER',
    sasl_mechanism='SCRAM-SHA-256',
    security_protocol='SASL_SSL',
    sasl_plain_username='YOUR_USERNAME',
    sasl_plain_password='YOUR_PASSWORD'
)
print('✅ Connected to Redpanda!')
producer.close()
"
```

---

## Alternative: Skip Redpanda for Now

If you can't find the connection details quickly, we can:

1. **Use fallback logging** - Events logged to file instead of Redpanda
2. **Demo without streaming** - Show architecture, explain Redpanda would be used in production
3. **Add Redpanda later** - Focus on other integrations first

Just let me know and I can update the code to work without Redpanda!

---

## Need Help?

**Common Issues:**

1. **"Can't find connection details"**
   - Look for "Connect" or "How to Connect" button
   - Check "Overview" or "Settings" tabs
   - Try "Kafka API" or "Bootstrap servers" section

2. **"No users created"**
   - Go to Security → SASL/SCRAM
   - Click "Create User"
   - Choose username/password
   - Save credentials

3. **"Broker address format"**
   - Should look like: `seed-abc123.cloud.redpanda.com:9092`
   - May have multiple brokers (use any one)
   - Port is usually `:9092` or `:9093`

---

**Once you have the details, paste them here and I'll update the .env file!**
