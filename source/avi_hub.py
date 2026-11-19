import csv, json, os, sys, shutil, tempfile, tkinter as tk, hashlib, hmac, uuid, math
from pathlib import Path
from datetime import datetime, timezone
from tkinter import ttk, messagebox, filedialog, simpledialog

EDITOR_USER='ZENTREK'
DEFAULT_EDITOR_PASSWORD='Zentrek'
OWNER_PASSKEY='ZEN'
FIELDS=['id','title','category','machine','symptoms','solution']
BASE=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent
DEFAULT=BASE/'Database'/'AVI_Database.csv'
STATUSES=['Running','Down','Maintenance','Idle','Attention']
STATUS_COLORS={'Running':'#39c99a','Down':'#ff6577','Maintenance':'#f6b75e','Idle':'#8193a8','Attention':'#ff875c'}
SYMBOLS=['▣','◆','●','▲','■','⬢','✚','⚙','▤','◉']
BG='#090e16'; PANEL='#151e2b'; TEXT='#edf3fb'; MUTED='#8d9caf'; AMBER='#ffad45'; EDGE='#283647'; SIDEBAR='#101722'
ISSUES={
 'Camera not detected': [('Is the camera visible in approved device diagnostics?', 'If not, record the camera ID and check approved connection/power procedures.'),('Does the camera application show an error code?', 'Record the exact error and search the knowledge base.')],
 'Program loading failed':[('Is the selected program path correct?', 'Verify against the approved program location; do not modify production programs.'),('Does the message identify a missing file or access error?', 'Record the exact message and follow approved escalation steps.')],
 'Lighting abnormal':[('Is the issue consistent across repeated inspections?', 'Record the affected station and compare with approved reference settings.'),('Is an alarm displayed?', 'Record the alarm before requesting maintenance.')],
 'Inspection result abnormal':[('Is the correct approved inspection program selected?', 'Verify program identity with the authorized process owner.'),('Does the issue repeat on multiple samples?', 'Document observations and escalate per site procedure.')]
}
class App:
 def __init__(self,root):
  self.root=root;self.root.title('ZENTREK  /  AVI Knowledge Hub V4.1 Preview');self.root.geometry('1240x790');self.root.minsize(1000,680);self.root.configure(bg=BG)
  self.editor_unlocked=False;self.editor_password_hash=self.hash_secret(DEFAULT_EDITOR_PASSWORD);self.load_editor_password()
  self.rows=[];self.path=DEFAULT;self.dirty=False;self.layout_dirty=False;self.machine='AVI-01';self.view='Dashboard'
  self.heartbeat_cache={};self.refresh_job=None;self.machines=[];self.notes=[];self.shapes=[];self.floor_mode='Schematic';self.floor_zoom=1.0;self.layout_path=None;self.drag=None;self.edit_floor=False;self.load_layout()
  self.style=ttk.Style();self.style.theme_use('clam')
  self.style.configure('Treeview',background=PANEL,foreground=TEXT,fieldbackground=PANEL,rowheight=37,borderwidth=0,font=('Segoe UI',10))
  self.style.configure('Treeview.Heading',background='#263345',foreground=AMBER,font=('Segoe UI',10,'bold'),padding=10)
  self.style.map('Treeview',background=[('selected','#38485a')],foreground=[('selected','#ffffff')])
  self.style.configure('TCombobox',padding=7)
  self.sidebar=tk.Frame(root,bg=SIDEBAR,width=248);self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
  tk.Frame(self.sidebar,bg=AMBER,height=4).pack(fill='x')
  tk.Label(self.sidebar,text='◈  ZENTREK',bg=SIDEBAR,fg=AMBER,font=('Segoe UI',26,'bold')).pack(anchor='w',padx=22,pady=(29,1))
  tk.Label(self.sidebar,text='AVI  /  KNOWLEDGE HUB',bg=SIDEBAR,fg=MUTED,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=24,pady=(0,30))
  tk.Label(self.sidebar,text='WORKSPACE',bg=SIDEBAR,fg='#687a90',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=24,pady=(0,10))
  self.nav_buttons={}
  for name,caption in [('Dashboard','▦  Dashboard'),('Machine Registry','▤  Machine Registry'),('Troubleshooting Wizard','◇  Troubleshooting'),('Knowledge Base','▣  Knowledge Base')]:
   button=self.btn(self.sidebar,caption,lambda n=name:self.show(n));button.pack(fill='x',padx=13,pady=5);self.nav_buttons[name]=button
  tk.Frame(self.sidebar,bg=EDGE,height=1).pack(fill='x',padx=19,pady=(26,18))
  tk.Label(self.sidebar,text='DATABASE TOOLS',bg=SIDEBAR,fg='#687a90',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=24,pady=(0,10))
  self.btn(self.sidebar,'↻  Reconnect',self.reconnect).pack(fill='x',padx=13,pady=5)
  self.btn(self.sidebar,'▤  Open Other CSV',self.open_csv).pack(fill='x',padx=13,pady=5)
  self.btn(self.sidebar,'↓  Save Database',self.save).pack(fill='x',padx=13,pady=5)
  self.auth_button=self.btn(self.sidebar,'🔒  Unlock Editor',self.toggle_editor);self.auth_button.pack(fill='x',padx=13,pady=5)
  self.btn(self.sidebar,'⚿  Change Editor Password',self.change_editor_password).pack(fill='x',padx=13,pady=5)
  self.status=tk.Label(self.sidebar,text='',bg=SIDEBAR,fg=MUTED,wraplength=206,justify='left',font=('Segoe UI',9));self.status.pack(side='bottom',fill='x',padx=19,pady=24)
  self.main=tk.Frame(root,bg=BG);self.main.pack(side='left',fill='both',expand=True)
  self.root.protocol('WM_DELETE_WINDOW',self.close)
  self.reconnect()
 def hash_secret(self,value):
  return hashlib.sha256(value.encode('utf-8')).hexdigest()
 def password_file(self):
  return BASE/'Database'/'ZENTREK_Editor.json'
 def load_editor_password(self):
  try:
   p=self.password_file()
   if p.exists():
    data=json.loads(p.read_text(encoding='utf-8'))
    value=data.get('password_sha256','')
    if isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value):
     self.editor_password_hash=value
  except (OSError,ValueError,TypeError):
   pass
 def toggle_editor(self):
  if self.editor_unlocked:
   self.editor_unlocked=False;self.edit_floor=False
   self.auth_button.configure(text='🔒  Unlock Editor')
   self.show(self.view);return
  win=tk.Toplevel(self.root);win.title('ZENTREK / Editor Login');win.geometry('400x260');win.configure(bg=BG);win.transient(self.root);win.grab_set()
  self.label(win,'EDITOR AUTHENTICATION',14,AMBER,True).pack(anchor='w',padx=22,pady=(20,14))
  self.label(win,'USERNAME',10,MUTED).pack(anchor='w',padx=22)
  user=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat');user.pack(fill='x',padx=22,ipady=7);user.insert(0,EDITOR_USER)
  self.label(win,'PASSWORD',10,MUTED).pack(anchor='w',padx=22,pady=(10,0))
  password=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',show='*');password.pack(fill='x',padx=22,ipady=7);password.focus_set()
  def login(event=None):
   if hmac.compare_digest(user.get(),EDITOR_USER) and hmac.compare_digest(self.hash_secret(password.get()),self.editor_password_hash):
    self.editor_unlocked=True;self.auth_button.configure(text='🔓  Lock Editor');win.destroy();self.show(self.view)
   else:
    password.delete(0,'end');messagebox.showerror('Access denied','Incorrect editor credentials.',parent=win)
  password.bind('<Return>',login)
  self.btn(win,'Unlock Editor',login).pack(anchor='e',padx=22,pady=14)
 def require_editor(self):
  if self.editor_unlocked:return True
  messagebox.showwarning('Viewer Mode','Unlock Editor Mode before making changes.')
  return False
 def change_editor_password(self):
  win=tk.Toplevel(self.root);win.title('ZENTREK / Change Editor Password');win.geometry('420x305');win.configure(bg=BG);win.transient(self.root);win.grab_set()
  self.label(win,'OWNER AUTHORIZATION REQUIRED',13,AMBER,True).pack(anchor='w',padx=20,pady=(20,12))
  fields=[]
  for label in ('OWNER PASSKEY','NEW EDITOR PASSWORD','CONFIRM NEW PASSWORD'):
   self.label(win,label,10,MUTED).pack(anchor='w',padx=20,pady=(6,3))
   e=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',show='*')
   e.pack(fill='x',padx=20,ipady=6);fields.append(e)
  def commit():
   key,new,confirm=(e.get() for e in fields)
   if not hmac.compare_digest(key,OWNER_PASSKEY):
    messagebox.showerror('Denied','Invalid owner passkey.',parent=win);return
   if len(new)<8 or new!=confirm:
    messagebox.showerror('Invalid password','Password must contain at least 8 characters and both entries must match.',parent=win);return
   path=self.password_file()
   try:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.zentrek_auth_',suffix='.json',dir=str(path.parent))
    try:
     with os.fdopen(fd,'w',encoding='utf-8') as out:json.dump({'password_sha256':self.hash_secret(new)},out)
     os.replace(tmp,path)
    finally:
     if os.path.exists(tmp):os.unlink(tmp)
   except OSError as exc:
    messagebox.showerror('Password not saved',str(exc),parent=win);return
   self.editor_password_hash=self.hash_secret(new);self.editor_unlocked=False
   self.auth_button.configure(text='🔒  Unlock Editor')
   win.destroy();self.show(self.view)
   messagebox.showinfo('Password updated','Editor password changed. Log in again with the new password.')
  self.btn(win,'Authorize & Change Password',commit).pack(anchor='e',padx=20,pady=16)
 def btn(self,parent,label,command):
  return tk.Button(parent,text=label,command=command,bg='#202c3c',fg=TEXT,activebackground='#3a485b',activeforeground=AMBER,relief='flat',anchor='w',cursor='hand2',padx=17,pady=12,font=('Segoe UI',10,'bold'),bd=0,highlightthickness=0)
 def label(self,parent,text,size=11,color=TEXT,bold=False):
  return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),anchor='w',justify='left')
 def clear(self):
  for child in self.main.winfo_children():child.destroy()
 def heading(self,title,subtitle=''):
  self.label(self.main,'ZENTREK  /  PRODUCTION OPERATIONS',9,AMBER,True).pack(anchor='w',padx=30,pady=(26,8))
  self.label(self.main,title,26,TEXT,True).pack(anchor='w',padx=30,pady=(0,5))
  self.label(self.main,subtitle,10,MUTED).pack(anchor='w',padx=30,pady=(0,20))
  tk.Frame(self.main,bg=EDGE,height=1).pack(fill='x',padx=30,pady=(0,14))
 def show(self,view):
  if self.refresh_job is not None:
   self.root.after_cancel(self.refresh_job);self.refresh_job=None
  self.view=view;self.clear()
  for name,button in self.nav_buttons.items():button.configure(bg='#3a3028' if name==view else '#202c3c',fg=AMBER if name==view else TEXT)
  if view=='Dashboard':self.dashboard()
  elif view=='Machine Registry':self.registry()
  elif view=='Troubleshooting Wizard':self.wizard()
  else:self.knowledge()
  if view=='Machine Registry':self.schedule_floor_refresh()
 def layout_file(self):
  return self.path.parent/'ZENTREK_Floorplan.json'
 def default_machines(self):
  return [{'id':f'AVI-{i:02d}','name':f'AVI {i:02d}','status':'Idle','symbol':'▣','x':0.07+((i-1)%7)*0.14,'y':0.12+((i-1)//7)*0.23} for i in range(1,27)]
 def load_layout(self):
  self.layout_path=self.layout_file()
  try:
   if self.layout_path.exists():
    with open(self.layout_path,encoding='utf-8') as f:data=json.load(f)
    self.machines=data.get('machines',self.default_machines())
    self.notes=data.get('notes',[]);self.shapes=data.get('shapes',[])
    if not isinstance(self.machines,list) or not isinstance(self.notes,list):raise ValueError('Invalid layout data')
   else:self.machines=self.default_machines();self.notes=[];self.shapes=[]
   self.layout_dirty=False
  except Exception as e:
   self.machines=self.default_machines();self.notes=[];self.shapes=[]
   messagebox.showwarning('Layout load issue',f'Using default floor plan. Existing file was not overwritten.\n{e}')
 def save_layout(self,quiet=False):
  if not self.require_editor():return
  path=self.layout_file();lock=Path(str(path)+'.lock')
  try:
   path.parent.mkdir(parents=True,exist_ok=True)
   fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
  except Exception as e:
   messagebox.showerror('Layout save blocked',str(e));return False
  try:
   if path.exists():
    backup=path.with_name(path.stem+'_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json')
    shutil.copy2(path,backup)
   fd,tmp=tempfile.mkstemp(prefix='.zentrek_',suffix='.json',dir=str(path.parent))
   try:
    with os.fdopen(fd,'w',encoding='utf-8') as out:
     json.dump({'version':1,'machines':self.machines,'notes':self.notes,'shapes':self.shapes},out,ensure_ascii=False,indent=2)
    os.replace(tmp,path)
   finally:
    if os.path.exists(tmp):os.unlink(tmp)
   self.layout_dirty=False
   if not quiet:messagebox.showinfo('Saved','Floor plan, machine statuses and pinboard saved.')
   return True
  except Exception as e:messagebox.showerror('Layout save failed',str(e));return False
  finally:
   try:lock.unlink()
   except OSError:pass
 def dashboard(self):
  self.heading('Production overview','Manual machine status, immediate-attention pinboard and knowledge overview')
  bar=tk.Frame(self.main,bg=BG);bar.pack(fill='x',padx=25,pady=(0,14))
  attention=sum(m.get('status') in ('Down','Attention') for m in self.machines)
  for title,val,sub in [('MACHINES',str(len(self.machines)),'Editable floor registry'),('NEED ATTENTION',str(attention),'Down or attention'),('ARTICLES',str(len(self.rows)),'Knowledge records'),('DATABASE','READY' if self.path.exists() else 'MISSING','Shared CSV')]:
   tile=tk.Frame(bar,bg=PANEL,padx=15,pady=17,highlightbackground=EDGE,highlightthickness=1);tile.pack(side='left',fill='both',expand=True,padx=4)
   self.label(tile,title,9,MUTED,True).pack(anchor='w')
   self.label(tile,val,22,AMBER if title!='NEED ATTENTION' or attention==0 else '#ff6577',True).pack(anchor='w',pady=5)
   self.label(tile,sub,9,MUTED).pack(anchor='w')
  top=tk.Frame(self.main,bg=BG);top.pack(fill='x',padx=30,pady=(9,8))
  self.label(top,'📌  IMMEDIATE ATTENTION  /  PINBOARD',13,AMBER,True).pack(side='left')
  self.btn(top,'+ Pin Note',self.add_note).pack(side='right')
  board=tk.Frame(self.main,bg=BG);board.pack(fill='both',expand=True,padx=26)
  if not self.notes:self.label(board,'No pinned notes. Add a priority reminder for the production team.',11,MUTED).pack(anchor='w',padx=8,pady=15)
  for i,note in enumerate(self.notes):
   card=tk.Frame(board,bg='#263043',padx=13,pady=10,highlightbackground=EDGE,highlightthickness=1);card.pack(fill='x',padx=4,pady=4)
   header=tk.Frame(card,bg='#263043');header.pack(fill='x')
   self.label(header,'●  '+note.get('title','Attention'),11,AMBER,True).pack(side='left')
   tk.Button(header,text='✕',command=lambda j=i:self.delete_note(j),bg='#263043',fg='#ff8996',relief='flat',cursor='hand2').pack(side='right')
   self.btn(header,'Edit',lambda j=i:self.add_note(j)).pack(side='right',padx=7)
   self.label(card,note.get('body',''),10,TEXT).pack(anchor='w',pady=(4,0))
  self.label(self.main,'Statuses and notes are manually maintained, not live telemetry.',9,MUTED).pack(anchor='w',padx=30,pady=(8,12))
 def add_note(self,index=None):
  if not self.require_editor():return
  old=self.notes[index] if index is not None else {}
  win=tk.Toplevel(self.root);win.title('Immediate Attention Pin');win.geometry('490x370');win.configure(bg=BG);win.transient(self.root);win.grab_set()
  self.label(win,'PIN TITLE',11,AMBER,True).pack(anchor='w',padx=20,pady=(20,6))
  title=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',12));title.pack(fill='x',padx=20,ipady=8);title.insert(0,old.get('title',''))
  self.label(win,'NOTE / ACTION',11,AMBER,True).pack(anchor='w',padx=20,pady=(16,6))
  body=tk.Text(win,height=7,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',wrap='word');body.pack(fill='both',expand=True,padx=20);body.insert('1.0',old.get('body',''))
  def commit():
   if not title.get().strip():messagebox.showwarning('Missing title','Enter a title.',parent=win);return
   note={'title':title.get().strip(),'body':body.get('1.0','end').strip()}
   if index is None:self.notes.insert(0,note)
   else:self.notes[index]=note
   self.layout_dirty=True;win.destroy();self.save_layout(quiet=True);self.show('Dashboard')
  self.btn(win,'Save Pin',commit).pack(anchor='e',padx=20,pady=12)
 def delete_note(self,index):
  if not self.require_editor():return
  if messagebox.askyesno('Remove pin','Remove this immediate-attention note?'):
   self.notes.pop(index);self.layout_dirty=True;self.save_layout(quiet=True);self.show('Dashboard')
 def read_heartbeat(self,mid):
  if not mid or Path(mid).name!=mid:return {'state':'Unknown','reason':'Invalid machine ID'}
  path=self.path.parent/'Heartbeats'/(mid+'.json')
  try:
   if path.stat().st_size>8192:raise ValueError('Heartbeat too large')
   data=json.loads(path.read_text(encoding='utf-8'))
   timestamp=datetime.fromisoformat(str(data['timestamp_utc']).replace('Z','+00:00'))
   if timestamp.tzinfo is None:raise ValueError('Timestamp missing timezone')
   age=(datetime.now(timezone.utc)-timestamp.astimezone(timezone.utc)).total_seconds()
   if age< -120 or age>120:return {'state':'Unknown','reason':'Heartbeat stale or clock mismatch'}
   running=data.get('smartvision_running')
   if not isinstance(running,bool):raise ValueError('Invalid process state')
   return {'state':'Running' if running else 'Stopped','reason':'Heartbeat '+str(int(age))+'s ago','timestamp':str(data['timestamp_utc'])}
  except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
   return {'state':'Unknown','reason':'No valid recent heartbeat'}
 def schedule_floor_refresh(self):
  def refresh():
   self.refresh_job=None
   if self.view=='Machine Registry':
    self.draw_floor();self.schedule_floor_refresh()
  self.refresh_job=self.root.after(15000,refresh)
 def machine_detail(self,mid):
  m=self.machine_by_id(mid)
  if not m:return
  win=tk.Toplevel(self.root);win.title('ZENTREK / '+str(m.get('name',mid)));win.geometry('730x590');win.configure(bg=BG)
  state=self.read_heartbeat(mid)
  self.label(win,str(m.get('name',mid))+' / '+mid,19,AMBER,True).pack(anchor='w',padx=22,pady=(22,8))
  self.label(win,'SmartVision: '+state['state']+'   •   '+state['reason'],12,TEXT,True).pack(anchor='w',padx=22,pady=(0,9))
  self.label(win,'Manual floor status: '+str(m.get('status','Idle')),10,MUTED).pack(anchor='w',padx=22,pady=(0,14))
  self.label(win,'MACHINE KNOWLEDGE',12,AMBER,True).pack(anchor='w',padx=22,pady=(5,8))
  items=[r for r in self.rows if str(r.get('machine','')).strip().casefold() in (mid.casefold(),str(m.get('name','')).strip().casefold())]
  listing=tk.Listbox(win,bg=PANEL,fg=TEXT,selectbackground='#394e63',relief='flat',font=('Segoe UI',11))
  listing.pack(fill='both',expand=True,padx=22,pady=5)
  for r in items:listing.insert('end',r.get('title','Untitled'))
  article=tk.Text(win,height=9,bg=PANEL,fg=TEXT,wrap='word',relief='flat',font=('Segoe UI',10));article.pack(fill='both',expand=True,padx=22,pady=8)
  def show_article(event=None):
   if not listing.curselection():return
   r=items[listing.curselection()[0]]
   article.configure(state='normal');article.delete('1.0','end')
   article.insert('end','SYMPTOMS\n'+r.get('symptoms','')+'\n\nSOLUTION\n'+r.get('solution',''))
   article.configure(state='disabled')
  listing.bind('<<ListboxSelect>>',show_article)
  if not items:self.label(win,'No linked articles yet. Add articles using this machine ID.',10,MUTED).pack(anchor='w',padx=22)
  self.btn(win,'Refresh SmartVision Status',lambda:self.refresh_machine_detail(win,mid)).pack(anchor='e',padx=22,pady=10)
 def refresh_machine_detail(self,win,mid):
  win.destroy();self.machine_detail(mid)
 def registry(self):
  self.heading('Production floor planner','SmartVision heartbeat monitoring • click a machine to view its knowledge')
  states=[self.read_heartbeat(m['id'])['state'] for m in self.machines]
  counts=tk.Frame(self.main,bg=BG);counts.pack(fill='x',padx=30,pady=(0,8))
  for label,count in [('RUNNING',states.count('Running')),('STOPPED',states.count('Stopped')),('UNKNOWN',states.count('Unknown'))]:
   self.label(counts,label+': '+str(count),11,AMBER if label=='UNKNOWN' else TEXT,True).pack(side='left',padx=(0,20))
  controls=tk.Frame(self.main,bg=BG);controls.pack(fill='x',padx=30,pady=(0,9))
  self.btn(controls,'✓ Finish Editing' if self.edit_floor else '✥ Edit Layout',self.toggle_floor).pack(side='left',padx=(0,7))
  self.btn(controls,'+ Add Machine',self.add_machine).pack(side='left',padx=7)
  self.btn(controls,'◈ '+self.floor_mode+' View',self.switch_floor_mode).pack(side='left',padx=5)
  self.btn(controls,'+ Zone',lambda:self.add_floor_shape('zone')).pack(side='left',padx=4)
  self.btn(controls,'+ Label',lambda:self.add_floor_shape('label')).pack(side='left',padx=4)
  self.btn(controls,'+ Wall',lambda:self.add_floor_shape('wall')).pack(side='left',padx=4)
  self.btn(controls,'Zoom +',lambda:self.zoom_floor(1.2)).pack(side='left',padx=2)
  self.btn(controls,'Zoom -',lambda:self.zoom_floor(1/1.2)).pack(side='left',padx=2)
  self.btn(controls,'Save Floor Plan',self.save_layout).pack(side='right')
  self.label(self.main,'● Green = SmartVision running     ● Red = stopped     ● Grey = no fresh heartbeat     |     Manual status is separate',9,MUTED).pack(anchor='w',padx=30,pady=(0,7))
  self.floor=tk.Canvas(self.main,bg='#121d2b',highlightthickness=1,highlightbackground=EDGE,height=420,cursor='crosshair' if self.edit_floor else 'arrow')
  self.floor.pack(fill='both',expand=True,padx=30,pady=(0,12))
  self.floor.bind('<Configure>',lambda e:self.draw_floor())
  self.floor.bind('<ButtonPress-1>',self.floor_press)
  self.floor.bind('<B1-Motion>',self.floor_drag)
  self.floor.bind('<ButtonRelease-1>',self.floor_release)
  self.draw_floor()
  detail=tk.Frame(self.main,bg=BG);detail.pack(fill='x',padx=30,pady=(0,14))
  m=self.machine_by_id(self.machine)
  if m:
   self.label(detail,f"SELECTED: {m['name']}  /  {m['id']}  /  {m.get('status','Idle')}",12,AMBER,True).pack(side='left')
   self.btn(detail,'Edit Machine',lambda:self.edit_machine(m['id'])).pack(side='right')
   self.btn(detail,'Add Knowledge',lambda:self.edit_record(machine=m['id'])).pack(side='right',padx=7)
 def machine_by_id(self,mid):
  return next((m for m in self.machines if m.get('id')==mid),None)
 def toggle_floor(self):
  if not self.require_editor():return
  self.edit_floor=not self.edit_floor;self.show('Machine Registry')
 def switch_floor_mode(self):
  self.floor_mode='Visual' if self.floor_mode=='Schematic' else 'Schematic'
  self.show('Machine Registry')
 def zoom_floor(self,factor):
  self.floor_zoom=max(.7,min(1.8,self.floor_zoom*factor));self.draw_floor()
 def add_floor_shape(self,kind):
  if not self.require_editor():return
  label=simpledialog.askstring('Floor object','Enter a label for the '+kind+':',parent=self.root)
  if label is None:return
  self.shapes.append({'id':uuid.uuid4().hex[:12],'type':kind,'label':label.strip(),'x':.5,'y':.5})
  self.layout_dirty=True;self.edit_floor=True;self.show('Machine Registry')
 def draw_floor(self):
  if not hasattr(self,'floor') or not self.floor.winfo_exists():return
  c=self.floor;c.delete('all');w=max(c.winfo_width(),550);h=max(c.winfo_height(),320)
  for x in range(0,w,40):c.create_line(x,0,x,h,fill='#1c2b3b')
  for y in range(0,h,40):c.create_line(0,y,w,y,fill='#1c2b3b')
  c.create_text(17,15,text='PRODUCTION FLOOR  /  CUSTOM LAYOUT',fill='#72869b',anchor='nw',font=('Segoe UI',10,'bold'))
  for shape in self.shapes:
   try:
    x=float(shape.get('x',.5))*w;y=float(shape.get('y',.5))*h;kind=shape.get('type');label=str(shape.get('label',''))[:45]
    if kind=='zone':c.create_rectangle(x-75,y-34,x+75,y+34,fill='#202f40',outline='#63809c',dash=(5,4),tags=('shape',shape['id']));c.create_text(x,y,text=label,fill='#a5b9ce',tags=('shape',shape['id']))
    elif kind=='wall':c.create_line(x-70,y,x+70,y,fill='#71859a',width=7,tags=('shape',shape['id']))
    else:c.create_text(x,y,text=label,fill=AMBER,font=('Segoe UI',11,'bold'),tags=('shape',shape['id']))
   except (ValueError,TypeError,KeyError):continue
  for m in self.machines:
   x=max(35,min(w-35,float(m.get('x',.5))*w*self.floor_zoom));y=max(45,min(h-28,float(m.get('y',.5))*h*self.floor_zoom))
   mid=m['id'];heartbeat=self.read_heartbeat(mid);live=heartbeat['state'];color={'Running':'#39c99a','Stopped':'#ff6577','Unknown':'#8193a8'}[live];selected=mid==self.machine
   c.create_rectangle(x-45,y-23,x+45,y+26,fill=('#455466' if self.floor_mode=='Visual' else '#334354') if selected else ('#304154' if self.floor_mode=='Visual' else '#1c2b3b'),outline=AMBER if selected else color,width=2 if selected else 1,tags=('machine',mid))
   if self.floor_mode=='Visual':c.create_rectangle(x-34,y-17,x+34,y-3,fill='#647b91',outline='#a3b6c8',tags=('machine',mid))
   c.create_text(x,y-7,text=str(m.get('symbol','▣')),fill=color,font=('Segoe UI Symbol',17,'bold'),tags=('machine',mid))
   c.create_text(x,y+13,text=str(m.get('name',mid))[:17],fill=TEXT,font=('Segoe UI',9,'bold'),tags=('machine',mid))
   c.create_text(x,y+36,text=live,fill=color,font=('Segoe UI',8,'bold'),tags=('machine',mid))
  if self.edit_floor:c.create_text(w-12,15,text='EDIT MODE  •  DRAG TO MOVE',anchor='ne',fill=AMBER,font=('Segoe UI',9,'bold'))
 def floor_press(self,event):
  tags=self.floor.gettags('current');mid=tags[1] if len(tags)>1 and tags[0] in ('machine','shape') else None
  if not mid:return
  if tags[0]=='shape':
   self.drag={'id':mid,'kind':'shape','moved':False};return
  self.machine=mid;self.drag={'id':mid,'moved':False,'x':event.x,'y':event.y};self.draw_floor()
 def floor_drag(self,event):
  if not self.drag or not self.edit_floor:return
  m=next((v for v in self.shapes if v.get('id')==self.drag['id']),None) if self.drag.get('kind')=='shape' else self.machine_by_id(self.drag['id'])
  if not m:return
  w=max(self.floor.winfo_width(),1);h=max(self.floor.winfo_height(),1)
  m['x']=max(.06,min(.94,event.x/(w*self.floor_zoom)));m['y']=max(.12,min(.92,event.y/(h*self.floor_zoom)))
  self.drag['moved']=True;self.layout_dirty=True;self.draw_floor()
 def floor_release(self,event):
  if not self.drag:return
  moved=self.drag['moved'];mid=self.drag['id'];self.drag=None
  if not moved and self.drag is None and any(v.get('id')==mid for v in self.shapes):
   if self.edit_floor and messagebox.askyesno('Remove shape','Remove selected floor shape?'):
    self.shapes=[v for v in self.shapes if v.get('id')!=mid];self.layout_dirty=True;self.show('Machine Registry')
  elif not moved:
   if self.edit_floor:self.edit_machine(mid)
   else:self.machine_detail(mid)
  else:self.show('Machine Registry')
 def add_machine(self):
  if not self.require_editor():return
  ids={m['id'] for m in self.machines};n=1
  while f'AVI-{n:02d}' in ids:n+=1
  mid=f'AVI-{n:02d}'
  self.machines.append({'id':mid,'name':f'AVI {n:02d}','status':'Idle','symbol':'▣','x':.5,'y':.5})
  self.machine=mid;self.layout_dirty=True;self.edit_machine(mid)
 def edit_machine(self,mid):
  if not self.require_editor():return
  m=self.machine_by_id(mid)
  if not m:return
  win=tk.Toplevel(self.root);win.title('Machine Properties');win.geometry('475x455');win.configure(bg=BG);win.transient(self.root);win.grab_set()
  self.label(win,'MACHINE ID  /  '+mid,12,AMBER,True).pack(anchor='w',padx=22,pady=(20,13))
  self.label(win,'DISPLAY NAME',10,MUTED).pack(anchor='w',padx=22)
  name=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',12));name.pack(fill='x',padx=22,pady=(4,12),ipady=7);name.insert(0,m.get('name',mid))
  self.label(win,'MANUAL STATUS',10,MUTED).pack(anchor='w',padx=22)
  status=tk.StringVar(value=m.get('status','Idle'));ttk.Combobox(win,textvariable=status,values=STATUSES,state='readonly').pack(fill='x',padx=22,pady=(4,12))
  self.label(win,'FLOOR SYMBOL  /  PICK OR TYPE YOUR OWN',10,MUTED).pack(anchor='w',padx=22)
  symbol=tk.StringVar(value=m.get('symbol','▣'));ttk.Combobox(win,textvariable=symbol,values=SYMBOLS).pack(fill='x',padx=22,pady=(4,12))
  self.label(win,'The stable machine ID stays unchanged to preserve knowledge links.',9,MUTED).pack(anchor='w',padx=22,pady=6)
  actions=tk.Frame(win,bg=BG);actions.pack(fill='x',padx=22,pady=15)
  def commit():
   if not name.get().strip() or not symbol.get().strip():messagebox.showwarning('Required','Name and symbol are required.',parent=win);return
   m.update(name=name.get().strip(),status=status.get(),symbol=symbol.get().strip()[:4]);self.layout_dirty=True
   win.destroy();self.save_layout(quiet=True);self.show('Machine Registry')
  self.btn(actions,'Save Changes',commit).pack(side='left')
  def remove():
   if not messagebox.askyesno('Remove machine','Remove this machine from the floor registry? Knowledge records remain.',parent=win):return
   self.machines.remove(m);self.machine=self.machines[0]['id'] if self.machines else '';self.layout_dirty=True;win.destroy();self.save_layout(quiet=True);self.show('Machine Registry')
  self.btn(actions,'Remove Machine',remove).pack(side='right')
 def choose_machine(self,m):self.machine=m;self.show('Machine Registry')
 def wizard(self):
  self.heading('GUIDED TROUBLESHOOTING','Interactive decision paths and site-approved guidance')
  wrap=tk.Frame(self.main,bg=PANEL,padx=24,pady=20);wrap.pack(fill='both',expand=True,padx=30,pady=10)
  flows=self.load_wizard_flows()
  self.label(wrap,'Select symptom',12,AMBER,True).pack(anchor='w')
  issue=tk.StringVar(value=next(iter(flows),''))
  ttk.Combobox(wrap,textvariable=issue,values=list(flows),state='readonly',width=42).pack(anchor='w',pady=12)
  self.label(wrap,'Machine ID',11,MUTED).pack(anchor='w')
  machine=tk.StringVar(value=self.machine)
  ttk.Combobox(wrap,textvariable=machine,values=[m['id'] for m in self.machines],state='readonly',width=18).pack(anchor='w',pady=8)
  question=self.label(wrap,'',14,TEXT,True);question.pack(anchor='w',pady=12)
  guidance=self.label(wrap,'',11,MUTED);guidance.pack(anchor='w',pady=10)
  state={'step':0,'answers':[]}
  def render():
   steps=flows.get(issue.get(),[])
   if not steps:question.configure(text='No diagnostic steps configured.');return
   n=min(state['step'],len(steps)-1);item=steps[n]
   question.configure(text=str(n+1)+'. '+item.get('question',''))
   guidance.configure(text=item.get('guidance','Select Yes or No to continue.'))
  def answer(value):
   steps=flows.get(issue.get(),[])
   if not steps:return
   item=steps[min(state['step'],len(steps)-1)]
   state['answers'].append((item.get('question',''),value))
   outcome=item.get(value.lower())
   if outcome:
    guidance.configure(text='OUTCOME: '+outcome+'\nRecord your observations and follow approved procedures.')
   elif state['step']+1<len(steps):
    state['step']+=1;render()
   else:guidance.configure(text='Checklist complete. Record observations or escalate as required.')
  def restart(*_):
   state['step']=0;state['answers']=[];render()
  issue.trace_add('write',restart)
  buttons=tk.Frame(wrap,bg=PANEL);buttons.pack(anchor='w',pady=15)
  self.btn(buttons,'YES',lambda:answer('YES')).pack(side='left',padx=5)
  self.btn(buttons,'NO',lambda:answer('NO')).pack(side='left',padx=5)
  self.btn(buttons,'Restart',restart).pack(side='left',padx=5)
  self.btn(buttons,'Edit Wizard Flow',self.edit_wizard_flow).pack(side='left',padx=5)
  self.btn(wrap,'Save as Knowledge Record',lambda:self.edit_record(machine=machine.get(),title=issue.get(),symptoms='; '.join(q+' = '+a for q,a in state['answers']))).pack(anchor='w',pady=6)
  render()
 def attachments_file(self):return self.path.parent/'Attachments.json'
 def load_attachments(self):
  try:
   p=self.attachments_file();return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
  except (OSError,ValueError):return {}
 def atomic_json(self,path,data):
  path.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(prefix='.zentrek_',suffix='.json',dir=str(path.parent))
  try:
   with os.fdopen(fd,'w',encoding='utf-8') as out:json.dump(data,out,indent=2,ensure_ascii=False)
   os.replace(tmp,path)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
 def add_attachment(self,article_id):
  if not self.require_editor():return
  src=filedialog.askopenfilename(filetypes=[('Approved media','*.png *.jpg *.jpeg *.gif *.pdf')])
  if not src:return
  source=Path(src)
  if source.suffix.lower() not in ('.png','.jpg','.jpeg','.gif','.pdf') or source.stat().st_size>15*1024*1024:
   messagebox.showerror('Attachment rejected','Use PNG, JPG, GIF or PDF up to 15 MB.');return
  directory=self.path.parent.parent/'Attachments'
  try:
   directory.mkdir(parents=True,exist_ok=True)
   name=uuid.uuid4().hex+source.suffix.lower()
   shutil.copy2(source,directory/name)
   data=self.load_attachments();data.setdefault(str(article_id),[]).append(name)
   self.atomic_json(self.attachments_file(),data)
   self.show('Knowledge Base')
  except OSError as exc:messagebox.showerror('Attachment error',str(exc))
 def open_attachment(self,name):
  if Path(name).name!=name:return
  path=self.path.parent.parent/'Attachments'/name
  if not path.is_file():messagebox.showwarning('Missing attachment','Attachment not found.');return
  if path.suffix.lower()=='.pdf':
   if sys.platform=='win32':os.startfile(str(path))
   else:messagebox.showinfo('PDF',str(path))
   return
  if path.suffix.lower() not in ('.png','.jpg','.jpeg','.gif'):return
  win=tk.Toplevel(self.root);win.title('ZENTREK / Image Preview');win.geometry('850x650');win.configure(bg=BG)
  try:
   img=tk.PhotoImage(file=str(path));win.image=img
   canvas=tk.Canvas(win,bg=BG,highlightthickness=0);canvas.pack(fill='both',expand=True)
   canvas.create_image(425,310,image=img)
  except tk.TclError:
   messagebox.showwarning('Preview unavailable','Image format not supported by this build.',parent=win);win.destroy()
 def wizard_file(self):return self.path.parent/'Wizard_Flows.json'
 def load_wizard_flows(self):
  try:
   p=self.wizard_file()
   if p.exists():
    data=json.loads(p.read_text(encoding='utf-8'))
    if isinstance(data,dict):return data
  except (OSError,ValueError):pass
  return {k:[{'question':q,'guidance':g} for q,g in values] for k,values in ISSUES.items()}
 def edit_wizard_flow(self):
  if not self.require_editor():return
  title=simpledialog.askstring('Wizard editor','Symptom / flow name:',parent=self.root)
  if not title:return
  question=simpledialog.askstring('Wizard editor','Diagnostic question:',parent=self.root)
  if not question:return
  yes=simpledialog.askstring('YES outcome','Approved guidance when YES:',parent=self.root)
  if yes is None:return
  no=simpledialog.askstring('NO outcome','Approved guidance when NO:',parent=self.root)
  if no is None:return
  flows=self.load_wizard_flows()
  flows[title.strip()]=[{'question':question.strip(),'yes':yes.strip(),'no':no.strip()}]
  try:self.atomic_json(self.wizard_file(),flows);self.show('Troubleshooting Wizard')
  except OSError as exc:messagebox.showerror('Wizard save failed',str(exc))
 def knowledge(self):
  self.heading('Knowledge library','Select an article to preview it instantly. Editing is a separate action.')
  tools=tk.Frame(self.main,bg=BG);tools.pack(fill='x',padx=28,pady=(2,10))
  query=tk.StringVar()
  entry=tk.Entry(tools,textvariable=query,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',12))
  entry.pack(side='left',fill='x',expand=True,ipady=10,padx=(0,12))
  self.btn(tools,'+ New Article',lambda:self.edit_record()).pack(side='left')
  body=tk.Frame(self.main,bg=BG);body.pack(fill='both',expand=True,padx=28,pady=(0,12))
  left=tk.Frame(body,bg=BG);left.pack(side='left',fill='both',expand=True,padx=(0,8))
  right=tk.Frame(body,bg=PANEL,highlightbackground=EDGE,highlightthickness=1,width=370)
  right.pack(side='right',fill='both',expand=True,padx=(8,0))
  tree=ttk.Treeview(left,columns=('id','title','machine','category'),show='headings',selectmode='browse')
  for col,w in [('id',55),('title',240),('machine',90),('category',105)]:
   tree.heading(col,text=col.upper());tree.column(col,width=w,stretch=col=='title')
  scroll=ttk.Scrollbar(left,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=scroll.set)
  scroll.pack(side='right',fill='y');tree.pack(side='left',fill='both',expand=True)
  self.label(right,'ARTICLE PREVIEW',10,AMBER,True).pack(anchor='w',padx=20,pady=(19,9))
  preview_title=self.label(right,'Select an article',17,TEXT,True);preview_title.pack(anchor='w',padx=20,pady=(0,10))
  meta=self.label(right,'Select a row to view details without editing.',10,MUTED);meta.pack(anchor='w',padx=20,pady=(0,14))
  preview=tk.Text(right,bg=PANEL,fg=TEXT,wrap='word',relief='flat',font=('Segoe UI',10),padx=20,pady=10,highlightthickness=0,cursor='arrow')
  preview.pack(fill='both',expand=True)
  preview.tag_configure('section',foreground=AMBER,font=('Segoe UI',10,'bold'),spacing1=12,spacing3=7)
  preview.tag_configure('content',foreground=TEXT,spacing3=8)
  preview.configure(state='disabled')
  def selected():
   selection=tree.selection()
   return int(selection[0]) if selection else None
  def update_preview(*_):
   idx=selected()
   preview.configure(state='normal');preview.delete('1.0','end')
   if idx is None or idx>=len(self.rows):
    preview_title.configure(text='Select an article')
    meta.configure(text='Click an article in the list to preview it.')
    preview.insert('end','No article selected.\n\nSearch the knowledge library, then select a row to read its symptoms and solution.')
   else:
    r=self.rows[idx]
    preview_title.configure(text=r.get('title','Untitled')[:70])
    meta.configure(text='ID: '+r.get('id','—')+'   •   '+r.get('machine','Any machine')+'   •   '+r.get('category','Uncategorized'))
    for heading,key in [('SYMPTOMS','symptoms'),('RECOMMENDED SOLUTION','solution')]:
     preview.insert('end',heading+'\n','section')
     preview.insert('end',(r.get(key,'').strip() or 'No information recorded.')+'\n\n','content')
    preview.insert('end','ATTACHMENTS (double-click filename to open)\n','section')
    for name in self.load_attachments().get(str(r.get('id','')),[]):preview.insert('end',name+'\n','content')
   preview.configure(state='disabled')
  def fill(*_):
   previous=tree.selection()
   for item in tree.get_children():tree.delete(item)
   q=query.get().strip().lower()
   for idx,r in enumerate(self.rows):
    if q in ' '.join(str(v) for v in r.values()).lower():
     tree.insert('','end',iid=str(idx),values=[r.get(c,'') for c in ('id','title','machine','category')])
   if previous and tree.exists(previous[0]):tree.selection_set(previous[0])
   elif tree.get_children():tree.selection_set(tree.get_children()[0])
   update_preview()
  def preview_open(event):
   idx=selected()
   if idx is None:return
   line=preview.get('insert linestart','insert lineend').strip()
   if line in self.load_attachments().get(str(self.rows[idx].get('id','')),[]):self.open_attachment(line)
  preview.bind('<Double-Button-1>',preview_open)
  tree.bind('<<TreeviewSelect>>',update_preview)
  tree.bind('<Double-1>',lambda event:update_preview())
  query.trace_add('write',fill)
  actions=tk.Frame(self.main,bg=BG);actions.pack(fill='x',padx=28,pady=(0,17))
  def edit():
   idx=selected()
   if idx is not None:self.edit_record(index=idx)
  def delete():
   if not self.require_editor():return
   idx=selected()
   if idx is not None and messagebox.askyesno('Delete article','Delete selected record?'):
    self.rows.pop(idx);self.dirty=True;self.show('Knowledge Base')
  self.btn(actions,'+ Attachment',lambda:self.add_attachment(self.rows[selected()].get('id','')) if selected() is not None else None).pack(side='left',padx=5)
  self.btn(actions,'✎  Edit Selected Article',edit).pack(side='left',padx=(0,8))
  self.btn(actions,'Delete Selected',delete).pack(side='left')
  self.label(actions,'Click = preview   •   Edit button = modify record',9,MUTED).pack(side='right')
  fill()
 def edit_record(self,index=None,machine='',title='',symptoms=''):
  if not self.require_editor():return
  old=self.rows[index] if index is not None else {}
  win=tk.Toplevel(self.root);win.title('Knowledge Record');win.geometry('650x610');win.configure(bg=BG);win.transient(self.root);win.grab_set()
  fields={}
  for key in FIELDS:
   self.label(win,key.upper(),10,MUTED).pack(anchor='w',padx=18,pady=(8,2))
   if key in ('symptoms','solution'):
    widget=tk.Text(win,height=5 if key=='solution' else 3,bg=PANEL,fg=TEXT,insertbackground=TEXT,wrap='word',relief='flat');widget.pack(fill='x',padx=18)
    widget.insert('1.0',old.get(key, symptoms if key=='symptoms' else ''))
   else:
    widget=tk.Entry(win,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));widget.pack(fill='x',padx=18,ipady=5)
    widget.insert(0,old.get(key, machine if key=='machine' else title if key=='title' else ''))
   fields[key]=widget
  def commit():
   row={k:(w.get('1.0','end').strip() if isinstance(w,tk.Text) else w.get().strip()) for k,w in fields.items()}
   if not row['title']:messagebox.showerror('Missing title','Article title is required.',parent=win);return
   if not row['id']:row['id']=str(max([int(r.get('id','0')) for r in self.rows if r.get('id','').isdigit()]+[0])+1)
   if index is None:self.rows.append(row)
   else:self.rows[index]=row
   self.dirty=True;win.destroy();self.show(self.view)
  self.btn(win,'Save Article',commit).pack(anchor='e',padx=18,pady=15)
 def reconnect(self):
  if DEFAULT.exists():self.load(DEFAULT)
  else:self.path=DEFAULT;self.rows=[];self.load_layout();self.status.config(text='Database missing:\n'+str(DEFAULT));self.show('Dashboard')
 def load(self,path):
  try:
   with open(path,'r',encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    if not set(FIELDS).issubset(reader.fieldnames or []):raise ValueError('CSV headers do not match expected schema')
    self.rows=[{k:r.get(k,'') for k in FIELDS} for r in reader]
   self.path=Path(path);self.dirty=False;self.load_layout();self.status.config(text='Connected:\n'+str(self.path));self.show(self.view)
  except Exception as e:messagebox.showerror('CSV load error',str(e))
 def open_csv(self):
  p=filedialog.askopenfilename(filetypes=[('CSV database','*.csv')])
  if p:self.load(p)
 def save(self):
  if not self.require_editor():return
  if not self.path.exists():
   messagebox.showwarning('Database missing','Create an approved CSV database at:\n'+str(self.path));return
  lock=Path(str(self.path)+'.lock')
  try:
   fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
  except FileExistsError:messagebox.showerror('Save blocked','Database save lock exists. Contact the designated editor.');return
  try:
   backup=self.path.with_name(self.path.stem+'_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.csv')
   shutil.copy2(self.path,backup)
   fd,tmp=tempfile.mkstemp(prefix='.avi_',suffix='.csv',dir=str(self.path.parent))
   try:
    with os.fdopen(fd,'w',encoding='utf-8',newline='') as f:
     writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(self.rows)
    os.replace(tmp,self.path)
   finally:
    if os.path.exists(tmp):os.unlink(tmp)
   self.dirty=False;self.status.config(text='Saved:\n'+str(self.path));messagebox.showinfo('Saved','Database saved and backup created.')
  except Exception as e:messagebox.showerror('Save failed',str(e))
  finally:
   try:lock.unlink()
   except OSError:pass
 def close(self):
  if (self.dirty or self.layout_dirty) and not messagebox.askyesno('Unsaved edits','Discard unsaved changes?'):return
  self.root.destroy()
if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
