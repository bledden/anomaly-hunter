# Airia Workflow Setup Guide

## Quick Answer
**You need to create a workflow in the Airia platform UI to get a workflow_id.**

## Step-by-Step Instructions

### 1. Access Airia Platform
- Go to: https://airia.com/ or https://explore.airia.com/
- Log in with your credentials using API key: `ak-NDE5MDE4MzMzM3wxNzYwNzM1NTE3OTIzfHRpLVJtRmphV3hwZEdGcGNpMVBjR1Z1SUZKbFoybHpkSEpoZEdsdmJpMVFjbTltWlhOemFXOXVZV3c9fDF8MTAwMzg2OTg3OSAg`

### 2. Create a Data Validation Workflow
1. Click **"Create Workflow"** or **"New Flow"**
2. Name it: `anomaly-data-validation`
3. Add workflow steps:
   - **Step 1**: Data Input (accepts JSON array of numbers)
   - **Step 2**: Validation Rules
     - Check for NaN values
     - Check for infinite values
     - Check for outliers
     - Calculate statistics (mean, std, min, max)
   - **Step 3**: Output quality score

### 3. Deploy Workflow
1. Click **"Deploy"** or **"Publish"**
2. The platform will generate a `workflow_id`
3. Copy this ID (format: UUID like `a1b2c3d4-e5f6-7890...`)

### 4. Get API Endpoint
The deployment should show an endpoint like:
```
POST https://api.airia.com/v1/workflows/{workflow_id}/execute
```

### 5. Update Code
Once you have the `workflow_id`, update `airia_workflows.py`:

```python
def __init__(self):
    self.api_key = os.getenv("AIRIA_API_KEY")
    self.workflow_id = "YOUR_WORKFLOW_ID_HERE"  # From Airia platform
    self.enabled = True if self.api_key and self.workflow_id else False
```

Then replace the local preprocessing with real API call:

```python
def preprocess_data(self, data: np.ndarray) -> Dict[str, Any]:
    if not self.enabled:
        return self._local_preprocessing(data)

    try:
        # Call Airia workflow API
        response = requests.post(
            f"https://api.airia.com/v1/workflows/{self.workflow_id}/execute",
            json={"data": data.tolist()},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"[AIRIA] 🔄 Preprocessed via cloud workflow")
            return result
        else:
            return self._local_preprocessing(data)
    except Exception as e:
        print(f"[WARN] Airia API failed: {e}")
        return self._local_preprocessing(data)
```

## Alternative: Use Airia's Data Validation API Directly

If you don't want to create a workflow, Airia might have a direct validation endpoint:

```python
# Check API docs at https://api.airia.ai/docs/
response = requests.post(
    "https://api.airia.com/v1/validate",
    json={
        "data": data.tolist(),
        "checks": ["nulls", "outliers", "statistics"]
    },
    headers={"Authorization": f"Bearer {self.api_key}"}
)
```

## Current Status

**Currently**: Using local preprocessing (100% functional, just not cloud-based)
**Why**: Need workflow_id from Airia platform
**Impact**: Low - local preprocessing works perfectly for demo

## For Hackathon Demo

You can say:
> "We built the Airia integration architecture. Currently it's using local preprocessing which works great, but we have the integration point ready - we'd just need to create a workflow in their platform to get the workflow_id and switch to cloud execution."

This is honest and shows you understand how the integration works!
