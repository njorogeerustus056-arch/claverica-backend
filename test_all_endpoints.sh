#!/bin/bash
echo "🔍 TESTING ALL PREVIOUSLY BROKEN ENDPOINTS..."
echo "============================================"

endpoints=(
    "transfers/transferrequest/"
    "payments/card/"
    "payments/payment/"
    "tasks/usertask/"
    "transactions/transaction/"
    "withdrawal/requests/"
    "receipts/receipt/"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "/admin/$endpoint ... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://claverica-backend-rniq.onrender.com/admin/$endpoint" 2>/dev/null || echo "000")
    
    if [ "$status" = "302" ]; then
        echo "✅ 302 (Redirect to login - WORKING!)"
    elif [ "$status" = "200" ]; then
        echo "✅ 200 (Direct access - WORKING!)"
    elif [ "$status" = "500" ]; then
        echo "❌ 500 (STILL BROKEN!)"
    else
        echo "⚠️  $status (Check manually)"
    fi
done
