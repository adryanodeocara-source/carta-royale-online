import json, os, random, secrets, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).parent
rooms={}; lock=threading.RLock(); COLORS=['red','blue','green','yellow']
def deck():
 d=[]
 for c in COLORS:
  d.append({'c':c,'v':'0'})
  for n in list(map(str,range(1,10)))+['skip','reverse','+2']:
   d.extend([{'c':c,'v':n} for _ in range(2)])
 for v in ['wild','+4']:
  d.extend([{'c':'wild','v':v} for _ in range(4)])
 random.shuffle(d);return d
def draw(s,n=1):
 out=[]
 for _ in range(n):
  if not s['deck']:
   recycled=s['discard'][:-1];s['discard']=s['discard'][-1:];random.shuffle(recycled);s['deck']=recycled
  if s['deck']:out.append(s['deck'].pop())
 return out
def public(s,token=''):
 p=next((p for p in s['players'] if p['token']==token),None)
 return {'code':s['code'],'started':s['started'],'finished':s['finished'],'players':[{'name':x['name'],'count':len(x['hand']),'uno':x['uno']} for x in s['players']],'turn':s['turn'],'top':s['discard'][-1] if s['discard'] else None,'color':s['color'],'direction':s['direction'],'pending_draw':s['pending_draw'],'logs':s['logs'][-8:],'hand':p['hand'] if p else None,'me':s['players'].index(p) if p else None,'admin':bool(token and secrets.compare_digest(token,s['admin'])),'deck_count':len(s['deck'])}
def next_turn(s,steps=1):s['turn']=(s['turn']+s['direction']*steps)%len(s['players'])
def action(data):
 a=data.get('action');code=str(data.get('room','')).upper();token=str(data.get('token',''))
 if a=='create':
  code=secrets.token_hex(3).upper();admin=secrets.token_urlsafe(24)
  rooms[code]={'code':code,'admin':admin,'players':[],'started':False,'finished':None,'deck':[],'discard':[],'color':None,'turn':0,'direction':1,'pending_draw':0,'logs':['Sala criada.'],'last_player':None}
  return {'ok':True,'code':code,'token':admin}
 s=rooms.get(code)
 if not s:raise ValueError('Sala não encontrada. Confira o código.')
 if a=='state':return {'ok':True,**public(s,token)}
 if a=='join':
  if s['started']:raise ValueError('Partida já começou.')
  if len(s['players'])>=6:raise ValueError('Limite de 6 jogadores.')
  name=str(data.get('name','')).strip()[:18]
  if not name:raise ValueError('Digite seu nome.')
  t=secrets.token_urlsafe(24);s['players'].append({'name':name,'token':t,'hand':[],'uno':False});s['logs'].append(name+' entrou na sala.')
  return {'ok':True,'token':t}
 if a in ('start','restart'):
  if not secrets.compare_digest(token,s['admin']):raise ValueError('Apenas o administrador pode iniciar ou reiniciar.')
  if len(s['players'])<2:raise ValueError('Entre com pelo menos 2 jogadores.')
  s.update(deck=deck(),discard=[],direction=1,turn=0,pending_draw=0,finished=None,started=True,last_player=None)
  for p in s['players']:p.update(hand=draw(s,7),uno=False)
  first=draw(s)[0]
  while first['c']=='wild' or first['v'] in ('skip','reverse','+2'):
   s['deck'].insert(0,first);first=draw(s)[0]
  s['discard']=[first];s['color']=first['c'];s['logs']=['Partida iniciada!'];return {'ok':True}
 p=next((p for p in s['players'] if p['token']==token),None)
 if not p:raise ValueError('Jogador não autorizado.')
 if not s['started'] or s['finished']:raise ValueError('A partida não está ativa.')
 i=s['players'].index(p)
 if a=='uno':
  if len(p['hand'])!=1:raise ValueError('Você só pode anunciar UNO com uma carta.')
  p['uno']=True;s['logs'].append(p['name']+' anunciou ÚLTIMA CARTA!');return {'ok':True}
 if i!=s['turn']:raise ValueError('Aguarde sua vez.')
 if a=='draw':
  count=s['pending_draw'] or 1;p['hand']+=draw(s,count);s['pending_draw']=0
  s['logs'].append(p['name']+' comprou '+str(count)+' carta(s).');next_turn(s);return {'ok':True}
 if a=='play':
  idx=data.get('index')
  if not isinstance(idx,int) or not 0<=idx<len(p['hand']):raise ValueError('Carta inválida.')
  card=p['hand'][idx];top=s['discard'][-1]
  if s['pending_draw']:raise ValueError('Você precisa comprar as cartas pendentes.')
  if not (card['c']=='wild' or card['c']==s['color'] or card['v']==top['v']):raise ValueError('Essa carta não pode ser jogada.')
  chosen=data.get('color')
  if card['c']=='wild' and chosen not in COLORS:raise ValueError('Escolha uma cor.')
  p['hand'].pop(idx);s['discard'].append(card);s['color']=chosen if card['c']=='wild' else card['c'];p['uno']=False
  s['logs'].append(p['name']+' jogou '+card['v']+'.')
  if not p['hand']:
   s['finished']=p['name'];s['logs'].append(p['name']+' venceu!');return {'ok':True}
  if card['v']=='reverse':s['direction']*=-1;next_turn(s,2 if len(s['players'])==2 else 1)
  elif card['v']=='skip':next_turn(s,2)
  elif card['v'] in ('+2','+4'):s['pending_draw']=2 if card['v']=='+2' else 4;next_turn(s)
  else:next_turn(s)
  return {'ok':True}
 raise ValueError('Ação desconhecida.')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kw):super().__init__(*args,directory=str(ROOT),**kw)
 def sendjson(self,obj,status=200):
  b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if urlparse(self.path).path=='/api/state':
   q=parse_qs(urlparse(self.path).query)
   with lock:
    try:self.sendjson(action({'action':'state','room':q.get('room',[''])[0],'token':q.get('token',[''])[0]}))
    except ValueError as e:self.sendjson({'error':str(e)},400)
   return
  if urlparse(self.path).path=='/':self.path='/index.html'
  return super().do_GET()
 def do_POST(self):
  if urlparse(self.path).path!='/api/action':return self.sendjson({'error':'Não encontrado'},404)
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<1 or n>8192:raise ValueError('Requisição inválida.')
   d=json.loads(self.rfile.read(n))
   with lock:r=action(d)
   self.sendjson(r)
  except (ValueError,TypeError,KeyError,IndexError,json.JSONDecodeError) as e:self.sendjson({'error':str(e)},400)
 def log_message(self,*args):pass
if __name__=='__main__':
 port=int(os.environ.get('PORT','8765'));print('CARTA ROYALE na porta',port,flush=True);ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
