const url = "https://apigw.hihumbird.com/oc/v2/orders/list";

const headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ2MjM3MiwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiMDliMGE0ZWMyNDVjNGE2MmE4YTQyNjNkYTIxMzk0NTAiLCJyZWxBcHBJZCI6MjYxNDA2OCwidXNlcklkIjoxMDM0MjI1LCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MTQwNzAsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6ImhhbG9vcG9kXzE4MTU3Nzc0NjI3In0.1VhsxMiwzMPxuOelBLbCN6yxpTCj4YM8PPAHiL3ogWl0qGeTbnVsezMPr5f7VnOus91EoL2qf4ATGH9Iz9LXOA",
    "Content-Type": "application/json;charset=UTF-8",
    "nonce": "431737",
    "sign": "99426e2f12dd0dd1f0e7dff114ea227151b5e3a0aa133093b800219f76970b2f",
    "stamp": "1770683541273"
};

const payload = {
    "order_ids": [
        "855050968218245633", "855051159763753473", "855051160032188929", 
        "855051160074131969", "855051159788919297", "855051078394288641", 
        "855021879277165059", "855021879277165059", "855021879277165059", 
        "855051040175757824", "855051040284809729", "855051040477747713", 
        "855051524458486273", "855050166300875265", "855050166468647425", 
        "853729576801671681", "853588637508573697", "853835257382738433", 
        "853638945005771265", "853608763557550593"
    ],
    "query_field_list": ["third_detail"]
};

async function getOrders() {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.result_code === "420") {
            console.error("❌ Signature Mismatch. Check if the payload matches exactly what generated the sign.");
        } else {
            console.log("✅ Data Received:", result);
        }
    } catch (error) {
        console.error("⚠️ Fetch Error:", error);
    }
}

getOrders();