import boto3, requests, uuid
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal, ROUND_HALF_UP

import const, token

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(const.DYNAMODB_TABLE_NAME)


def unitConvert(unit):
    if unit == "day":
        return "日"
    elif unit == "week":
        return "週"
    elif unit == "month":
        return "月"
    elif unit == "year":
        return "年"
    else:
        return "(不明)"


def pauseConvert(pause):
    
    return "停止中" if pause else "契約中"


def convertBodyParams(body):
    currency_select = body.get('currency_select', [None])[0]
    currency_other = body.get('currency_other', [None])[0]
    if currency_select == 'other':
        currency = currency_other
    else:
        currency = currency_select
    return {
        "token": body.get('token', [None])[0],
        "name": body.get('name', [None])[0],
        "price": body.get('price', [None])[0],
        "next_date": body.get('next_date', [None])[0],
        "interval": body.get('interval', [None])[0],
        "unit": body.get('unit', [None])[0],
        "payment_method": body.get('payment_method', [None])[0],
        "pause": "pause" in body.get('pause', [None]),
        "memo": body.get('memo', [None])[0],
        "currency": currency
    }


def verifyIdToken(id_token):
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    body = {
        'id_token': id_token,
        'client_id': const.CLIENT_ID
    }
    
    response = requests.post(
        const.LINE_ENDPOINT.VALIDATE_ID_TOKEN, 
        headers=headers, 
        data=body
    )
    
    return response.json()


def html_format(title="No Title", body="There is no contents.", script=""):

    style = """
    body {
        width: 100%;
        min-height: 100%;
        margin: 0;
        padding: 0;
        letter-spacing: 2px;
        font-family: sans-serif;
        font-weight: thin;
    }
    a {
        color: black;
        text-decoration: none;
    }
    main {
        min-height: 80%;
        padding: 5%;
        width: 90%;
    }
    .item {
        border: 1px solid #00008b;
        border-radius: 10px;
        padding: 5%;
        margin: 5% 0;
    }
    .item h2 {
        font-size: 20px;
    }
    .item .price {
        color: 
        font-size: 18px;
    }
    .item .next, .item .payment, .item .status {
        font-size: 13px;
    }
    .form-item {
        width: 90%;
        margin: 10% 0;
    }
    .form-item label {
        display: block;
    }
    .form-item input:not([type="checkbox"]), .form-item textarea, .form-item select, .form-item button {
        display: block;
        width: 100%;
        padding: 5%;
        border-radius: 10px;
        border: solid 1px #00008b;
        font-size: 16px;
        margin: 2% 0;
        color: black;
        background-color: white;
        letter-spacing: 2px;
    }
    .form-item input[type="submit"], .form-item button {
        width: fit-content;
        margin: auto;
    }
    .form-item .content {
        display: ruby;
    }
    .form-item .content p {
        width: fit-content;
    }
    .form-item .period .content input:not([type="checkbox"]) {
        width: 20%;
    }
    .form-item .period .content select {
        width: 30%;
    }
    .pause {
        display: flex;
    }
    .form-item .pause input {
        margin-right: 10px;
    }
    .delete button {
        color: white;
        background-color: #FF6961;
    }
    footer {
        padding: 5%;
        width: 90%;
        background-color: #00008b;
    }
    footer li {
        list-decoration: none;
    }
    footer a {
        color: white;
    }
    """

    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}｜サブスク通知</title>
            <style>{style}</style>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <main>
                <div id="fetch-content">{body}</div>
            </main>
            <footer>
                <ul>
                    <li><a class="link-params" href="/subscriptionLINEBotLIFF">登録したアイテム</a></li>
                    <li><a class="link-params" href="/subscriptionLINEBotLIFF/items/new">新規アイテム</a></li>
                </ul>
            </footer>
        </body>
        <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
        <script>{script}</script>
    </html>
    """



def formHtml(text):
    
    html = f"""
    <form method="post" id="send-form">
        <div class="form-item" style="display: none;">
            <input type="hidden" name="token" id="token">
        </div>
        <div class="form-item">
            <label>名前</label>
            <input type="text" name="name" id="name" required>
        </div>
        <div class="form-item">
            <label>通貨</label>
            <select name="currency_select" id="currency_select" required onchange="toggleCurrencyOther(this.value)">
                <option value="JPY">日本円（JPY）</option>
                <option value="USD">米ドル（USD）</option>
                <option value="EUR">ユーロ（EUR）</option>
                <option value="other">その他</option>
            </select>
        </div>
        <div class="form-item" id="currency_other_container" style="display: none;">
            <label>通貨コード (例: GBP)</label>
            <input type="text" name="currency_other" id="currency_other">
        </div>
        <div class="form-item">
            <label>料金</label>
            <input type="number" name="price" id="price" min="0" step="any" required>
        </div>
        <div class="form-item">
            <label>次回更新日</label>
            <input type="date" name="next_date" id="next_date" required>
        </div>
        <div class="form-item">
            <div class="period">
                <label>更新周期</label>
                <div class="content">
                    <input type="number" name="interval" id="interval" min="0" step="1" required>
                    <p>ヶ</p>
                    <select name="unit" required>
                        <option id="unit-day" value="day">日</option>
                        <option id="unit-week" value="week">週</option>
                        <option id="unit-month" value="month">月</option>
                        <option id="unit-year" value="year">年</option>
                    </select>
                    <p>毎</p>
                </div>
            </div>
        </div>
        <div class="form-item">
            <label>支払い方法</label>
            <input type="text" name="payment_method" id="payment_method" required>
        </div>
        <div class="form-item pause">
            <input type="checkbox" name="pause" id="pause" value="pause"><label>一時停止</label>
        </div>
        <div class="form-item">
            <label>メモ</label>
            <textarea id="memo" name="memo"></textarea>
        </div>
        <div class="form-item">
            <input type="submit" value="{text}">
        </div>
    </form>
    <script>
    function toggleCurrencyOther(value) {{
        var container = document.getElementById('currency_other_container');
        if (value === 'other') {{
            container.style.display = 'block';
        }} else {{
            container.style.display = 'none';
        }}
    }}
    </script>
    """
    
    if text == "更新":
        html += """
        <div class="form-item delete">
            <button onclick="delete_item()">削除</button>
        </div>
        """
    
    return html


def getUserItem():
    
    script = """
    let idToken, item_id;
    async function getUserData() {
        try {
			idToken = await liff.getIDToken();
            item_id = location.pathname.split("/").pop();
			const response = await fetch(`https://subscription.somando.jp/subscriptionLINEBotLIFF/api/items/${item_id}?token=${idToken}`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json'
				}
			});
			const data = await response.json();
            const item = data[0];
            console.log(item);
            document.getElementById('send-form').setAttribute('action', `https://subscription.somando.jp/subscriptionLINEBotLIFF/items/${item.id}`);
            document.getElementById('token').value = idToken;
            document.getElementById('name').value = item.name;
            document.getElementById('price').value = item.price;
            document.getElementById('next_date').value = item.next_date;
            document.getElementById('interval').value = item.interval;
            document.getElementById('unit-' + item.unit).selected = true;
            document.getElementById('payment_method').value = item.payment_method;
            document.getElementById('pause').checked = item.pause;
            document.getElementById('memo').value = item.memo ? item.memo : "";
            
            // 通貨フィールドの設定
            if (item.currency === "JPY" || item.currency === "USD" || item.currency === "EUR") {
                document.getElementById('currency_select').value = item.currency;
                document.getElementById('currency_other_container').style.display = 'none';
            } else {
                document.getElementById('currency_select').value = "other";
                document.getElementById('currency_other').value = item.currency;
                document.getElementById('currency_other_container').style.display = 'block';
            }
            
		} catch (error) {
			console.error(error);
			alert(error);
		}
    }
    async function delete_item() {
        if (confirm('削除しますか？')) {
            try {
                const response = await fetch(`https://subscription.somando.jp/subscriptionLINEBotLIFF/api/items/delete/${item_id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ token: idToken })
                });
                const data = await response.json();
                if (data.status) {
                    alert('削除しました。');
                    location.href = 'https://subscription.somando.jp/subscriptionLINEBotLIFF';
                } else {
                    alert('削除に失敗しました。');
                }
            } catch (error) {
                console.error(error);
                alert(error);
            }
        }
    }
    liff.init({ liffId: "2006629352-naO0NMkB" })
		.then(() => {
			if (!liff.isLoggedIn()) {
				liff.login();
			} else {
				getUserData();
			}
		})
    """
    
    html = html_format("アイテム詳細", formHtml("更新"), script)
    
    return html


def getUserItems():
    
    script = """
    let idToken;
    let exchangeRates = {};

    // 為替レートを取得する関数
    async function getExchangeRates() {
        try {
            const rateResponse = await fetch('https://api.exchangerate-api.com/v4/latest/JPY');
            const rateData = await rateResponse.json();
            if (!rateData.rates) {
                console.error("為替レート情報が取得できませんでした:", rateData);
                return {};
            }
            return rateData.rates;
        } catch (error) {
            console.error('Exchange rate error:', error);
            return {};
        }
    }

    function unit(word) {
        if (word === 'month') {
            return '月';
        } else if (word === 'year') {
            return '年';
        } else if (word === 'week') {
            return '週';
        } else if (word === 'day') {
            return '日';
        } else {
            return '';
        }
    }
    function pause(status) {
        return status ? '停止中' : '契約中';
    }

    async function getUserData() {
        try {
            idToken = await liff.getIDToken();
            // getExchangeRates() を呼び出して exchangeRates を設定
            exchangeRates = await getExchangeRates() || {};  
            const response = await fetch(`https://subscription.somando.jp/subscriptionLINEBotLIFF/api/items?token=${idToken}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            document.getElementById('fetch-content').innerHTML = "";
            data.forEach((item) => {
                document.getElementById('fetch-content').innerHTML += createItemElement(item);
            });
        } catch (error) {
            console.error(error);
            alert(error);
        }
    }

    function createItemElement(item) {
        let priceDisplay = "";
        if (item.currency === "JPY") {
            priceDisplay = "JPY " + Number(item.price).toLocaleString();
        } else {
            if (exchangeRates[item.currency]) {
                let factor = 1 / exchangeRates[item.currency];
                let converted = (item.price * factor).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                priceDisplay = item.currency + " " + Number(item.price).toFixed(2) + "（約 JPY " + converted + "）";
            } else {
                priceDisplay = item.currency + " " + Number(item.price).toFixed(2) + "（レート取得エラー）";
            }
        }
        return `
            <div class="item">
                <a href="https://subscription.somando.jp/subscriptionLINEBotLIFF/items/${item.id}">
                    <h2>${item.name}</h2>
                    <p class="price">${priceDisplay}</p>
                    <p class="next">次回請求日: ${item.next_date} (${item.interval}ヶ${unit(item.unit)}毎)</p>
                    <p class="payment">請求先: ${item.payment_method}</p>
                    <p class="status">ステータス: ${pause(item.pause)}</p>
                </a>
            </div>
        `;
    }

    liff.init({ liffId: "2006629352-naO0NMkB" })
        .then(() => {
            if (!liff.isLoggedIn()) {
                liff.login();
            } else {
                getUserData();
            }
        });
    """
    
    html = html_format("アイテム一覧", "Loading...", script)
    
    return html


def setUserItem(path_params, body, update=True):
    
    user = verifyIdToken(body.get("token"))
    user_id = user.get("sub", None)
    
    if user_id is None:
        return html_format("エラー", "ユーザーが照合できませんでした。")
    
    if update:
        item_id = path_params.get("item_id")
        response = table.query(
            KeyConditionExpression=Key('id').eq(item_id),
            FilterExpression=Attr('user').eq(user_id)
        )
        items = response.get('Items', [])
        
        if update and len(items) == 0:
            return html_format("エラー", "アイテムが見つかりませんでした。")
    else:
        item_id = str(uuid.uuid4())
    
    item_data = {
        'id': item_id,
        'user': user_id,
        'name': body.get("name"),
        'price': Decimal(str(body.get("price"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        'next_date': body.get("next_date"),
        'interval': int(body.get("interval")),
        'unit': body.get("unit"),
        'payment_method': body.get("payment_method"),
        'pause': bool(body.get("pause")),
        'currency': body.get("currency")
    }
    
    if body.get("memo"):
        item_data['memo'] = body.get("memo")
    
    table.put_item(
        Item=item_data
    )
    
    if item_data["currency"] == "JPY":
        price_str = "JPY " + format(int(item_data["price"]), ",")
    else:
        price_str = f'{item_data["currency"]} {float(item_data["price"]):.2f}'
    
    body_html = f"""
    {"更新" if update else "作成"}が完了しました。
    <div id="fetch-content">
        <div class="item">
            <h2>{item_data["name"]}</h2>
            <p class="price">{price_str}</p>
            <p class="next">次回請求日: {item_data["next_date"]} ({item_data["interval"]}ヶ{unitConvert(item_data["unit"])}毎)</p>
            <p class="payment">請求先: {item_data["payment_method"]}</p>
            <p class="status">ステータス: {pauseConvert(item_data["pause"])}</p>
        </div>
    </div>
    """
    
    return html_format("アイテム詳細" if update else "アイテム作成", body_html)


def newUserItem():
    
    script = """
    async function getUserData() {
        try {
			idToken = await liff.getIDToken();
            document.getElementById('token').value = idToken;
		} catch (error) {
			console.error(error);
			alert(error);
		}
    }
    liff.init({ liffId: "2006629352-naO0NMkB" })
		.then(() => {
			if (!liff.isLoggedIn()) {
				liff.login();
			} else {
				getUserData();
			}
		})
    """
    
    return html_format("新規アイテム", formHtml("作成"), script)


def route(path, method, params, path_params, body_params):

    if (path == "/subscriptionLINEBotLIFF" or path == "/subscriptionLINEBotLIFF/items") and method == "GET":
        
        html = getUserItems()
    
    elif (path == "/subscriptionLINEBotLIFF/items/{item_id}"):
        
        if method == "GET":
            
            html = getUserItem()
        
        elif method == "POST":
            
            body = convertBodyParams(body_params)
            print(body)
            
            html = setUserItem(path_params, body, True)
    
    elif path == "/subscriptionLINEBotLIFF/items/new":
        
        if method == "GET":
            
            html = newUserItem()
        
        elif method == "POST":
            
            body = convertBodyParams(body_params)
            
            html = setUserItem(path_params, body, False)
    
    return html
