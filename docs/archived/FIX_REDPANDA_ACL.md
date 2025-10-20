# Fix Redpanda ACL - 2 Minute Guide

## The Issue
```
[ERROR] Redpanda publish failed: [Error 29] TopicAuthorizationFailedError: anomaly-hunter-events
```

**Cause**: User `corch-admin` doesn't have WRITE permission on topic `anomaly-hunter-events`

## Quick Fix (2 minutes)

### Step 1: Go to Redpanda Console
Open: https://cloud.redpanda.com/clusters/d3pblnei82eh97tlk500/overview

### Step 2: Navigate to ACLs
1. Click **"Security"** in the left sidebar
2. Click **"Access Control"** or **"ACLs"**

### Step 3: Add WRITE Permission

**Option A: If topic exists**
1. Find topic: `anomaly-hunter-events`
2. Click **"Edit ACL"** or **"Manage Permissions"**
3. Add permission:
   - **Principal**: `User:corch-admin`
   - **Operation**: `WRITE` (check the box)
   - **Permission**: `ALLOW`
4. Click **"Save"**

**Option B: If topic doesn't exist (create it)**
1. Go to **"Topics"** tab
2. Click **"Create Topic"**
3. Name: `anomaly-hunter-events`
4. Partitions: `3` (default)
5. Replication: `3` (default)
6. Click **"Create"**
7. Then go to **Security → ACLs**
8. Add ACL:
   - **Resource Type**: `Topic`
   - **Resource Name**: `anomaly-hunter-events`
   - **Principal**: `User:corch-admin`
   - **Operations**: Check `WRITE`, `READ`, `DESCRIBE`
   - **Permission**: `ALLOW`
9. Click **"Add ACL"**

### Step 4: Test It
Run the detection again:
```bash
cd /Users/bledden/Documents/anomaly-hunter
python3 cli.py detect demo/data_database_spike.csv
```

**Look for:**
```
[REDPANDA] 📡 Event published to anomaly-hunter-events (severity 8/10)
  └─ Action: Streamed real-time anomaly event to Kafka topic
  └─ Result: Event contains 3 agent findings + context
```

## Alternative: Command Line Fix (if you have `rpk` CLI)

```bash
# Create topic
rpk topic create anomaly-hunter-events \
  --brokers d3pblnei82eh97tlk500.any.us-west-2.mpx.prd.cloud.redpanda.com:9092 \
  --tls-enabled \
  --sasl-mechanism SCRAM-SHA-256 \
  --user corch-admin \
  --password 'Facilitair1551Corch22$'

# Add ACL
rpk acl create \
  --allow-principal User:corch-admin \
  --operation write,read,describe \
  --topic anomaly-hunter-events \
  --brokers d3pblnei82eh97tlk500.any.us-west-2.mpx.prd.cloud.redpanda.com:9092 \
  --tls-enabled \
  --sasl-mechanism SCRAM-SHA-256 \
  --user corch-admin \
  --password 'Facilitair1551Corch22$'
```

## Verification

After fixing, you should see:
```
✅ [REDPANDA] Event published to anomaly-hunter-events
```

Instead of:
```
❌ [ERROR] Redpanda publish failed: TopicAuthorizationFailedError
```

---

**Ready?** Go to the Redpanda Console and add the WRITE permission now! Takes 30 seconds.
