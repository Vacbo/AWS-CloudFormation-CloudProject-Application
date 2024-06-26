from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
import boto3
from botocore.exceptions import ClientError
from typing import Annotated

# Initialize a DynamoDB resource and client.
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

app = FastAPI()

@app.get("/healthcheck", response_class=HTMLResponse)
async def healthcheck():
    return HTMLResponse(status_code=200)

@app.get("/", response_class=HTMLResponse)
async def read_bets():
    try:
        table = dynamodb.Table('BolaoTable')
        # Scan the table to get all bets
        response = table.scan()
                
        bets = response.get('Items', [])

        # Generate HTML content dynamically
        html_content = """
        <html><body>
        <h1>Bolão de atraso do Portella</h1>
        <ul>
        """

        # Add form for new bets
        html_content += """
        <h2>Apostar</h2>
        <form action="/add_bet" method="post">
            <label for="Name">Nome:</label>
            <input type="text" id="Name" name="name"><br><br>
            <label for="predicted_time">Horario de chegada (HH:MM):</label>
            <input type="time" id="predicted_time" name="predicted_time"><br><br>
            <button type="submit">Enviar aposta</button>
        </form>
        </body></html>
        """
        html_content += """<h2>Apostas já criadas</h2>"""
        for bet in bets:
            html_content += f"<li><span style=\"font-weight: bold;\">{bet['Name']}</span> aposta que o Portella vai chegar as <span style=\"font-weight: bold;\">{bet['predicted_time']}</span>  - <a href='/{bet['Name']}'>Deletar</a></li>"
        html_content += "</ul>"

        return HTMLResponse(content=html_content)
    except ClientError as e:
        return HTTPException(status_code=500, detail=str(e))

@app.get("/{name}", response_class=HTMLResponse) # ahref does not support DELETE method, so we use GET ;-;
async def delete_bet(name: str):
    table = dynamodb.Table('BolaoTable')
    # Delete the bet from the table.
    table.delete_item(Key={'Name': name})
    return HTMLResponse(content=f"<html><body><h1>Aposta deletada com sucesso!</h1><a href='/'>Voltar para a lista</a></body></html>")

@app.post("/add_bet", response_class=HTMLResponse)
async def add_bet(name: Annotated[str, Form()], predicted_time: Annotated[str, Form()]):

    table = dynamodb.Table('BolaoTable')

    table.update_item(
        Key={
            'Name': name,
        },
        UpdateExpression="set predicted_time = :time",
        ExpressionAttributeValues={
            ':time': predicted_time,
        },
        ReturnValues="UPDATED_NEW"
    )

    return HTMLResponse(content=f"<html><body><h1>Aposta adicionada com sucesso!</h1><a href='/'>Voltar para a lista</a></body></html>")
