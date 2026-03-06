#!/bin/bash
# Check FastAPI logs for crawl-related messages

echo "========================================"
echo "CHECKING FASTAPI LOGS FOR CRAWL ACTIVITY"
echo "========================================"
echo ""

echo "Last 50 lines of logs:"
echo "----------------------------------------"
sudo docker logs fastapi-backend --tail 50 2>&1 | grep -E "(Crawl|Knowledge Base|OpenSearch|Index|Error|Exception|agent_id|collection)" || echo "No crawl-related logs found"

echo ""
echo "========================================"
echo "To see full logs, run:"
echo "  sudo docker logs fastapi-backend --tail 200"
echo "========================================"
