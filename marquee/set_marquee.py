from bottle import post, redirect, request, route, run, template
import redis

client = redis.Redis()

@route('/')
def index():
    message = client.get('message')
    return template('<form action="/update" method="POST"><input type="text" name="message" value="{{message}}"><input type="submit"></form>', message=message)

@post('/update')
def update():
    new_text = request.forms.get('message')
    client.set('message', new_text)
    redirect("/")

run(host='localhost', port=8081, debug=True)
