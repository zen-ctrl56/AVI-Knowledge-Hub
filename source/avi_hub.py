import csv, os, sys, shutil, tempfile, tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

FIELDS=['id','title','category','machine','symptoms','solution']
BASE=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent
DEFAULT=BASE/'Database'/'AVI_Database.csv'
BG='#090e16'; PANEL='#151e2b'; TEXT='#edf3fb'; MUTED='#8d9caf'; AMBER='#ffad45'; EDGE='#283647'; SIDEBAR='#101722'
ISSUES={
 'Camera not detected': [('Is the camera visible in approved device diagnostics?', 'If not, record the camera ID and check approved connection/power procedures.'),('Does the camera application show an error code?', 'Record the exact error and search the knowledge base.')],
 'Program loading failed':[('Is the selected program path correct?', 'Verify against the approved program location; do not modify production programs.'),('Does the message identify a missing file or access error?', 'Record the exact message and follow approved escalation steps.')],
 'Lighting abnormal':[('Is the issue consistent across repeated inspections?', 'Record the affected station and compare with approved reference settings.'),('Is an alarm displayed?', 'Record the alarm before requesting maintenance.')],
 'Inspection result abnormal':[('Is the correct approved inspection program selected?', 'Verify program identity with the authorized process owner.'),('Does the issue repeat on multiple samples?', 'Document observations and escalate per site procedure.')]
}
class App:
 def __init__(self,root):
  self.root=root;self.root.title('AEGIS  /  AVI Knowledge Hub V3.1');self.root.geometry('1240x790');self.root.minsize(1000,680);self.root.configure(bg=BG)
  self.rows=[];self.path=DEFAULT;self.dirty=False;self.machine='AVI-01';self.view='Dashboard'
  self.style=ttk.Style();self.style.theme_use('clam')
  self.style.configure('Treeview',background=PANEL,foreground=TEXT,fieldbackground=PANEL,rowheight=37,borderwidth=0,font=('Segoe UI',10))
  self.style.configure('Treeview.Heading',background='#263345',foreground=AMBER,font=('Segoe UI',10,'bold'),padding=10)
  self.style.map('Treeview',background=[('selected','#38485a')],foreground=[('selected','#ffffff')])
  self.style.configure('TCombobox',padding=7)
  self.sidebar=tk.Frame(root,bg=SIDEBAR,width=248);self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
  tk.Frame(self.sidebar,bg=AMBER,height=4).pack(fill='x')
  tk.Label(self.sidebar,text='◈  AEGIS',bg=SIDEBAR,fg=AMBER,font=('Segoe UI',26,'bold')).pack(anchor='w',padx=22,pady=(29,1))
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
  self.status=tk.Label(self.sidebar,text='',bg=SIDEBAR,fg=MUTED,wraplength=206,justify='left',font=('Segoe UI',9));self.status.pack(side='bottom',fill='x',padx=19,pady=24)
  self.main=tk.Frame(root,bg=BG);self.main.pack(side='left',fill='both',expand=True)
  self.root.protocol('WM_DELETE_WINDOW',self.close)
  self.reconnect()
 def btn(self,parent,label,command):
  return tk.Button(parent,text=label,command=command,bg='#202c3c',fg=TEXT,activebackground='#3a485b',activeforeground=AMBER,relief='flat',anchor='w',cursor='hand2',padx=17,pady=12,font=('Segoe UI',10,'bold'),bd=0,highlightthickness=0)
 def label(self,parent,text,size=11,color=TEXT,bold=False):
  return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),anchor='w',justify='left')
 def clear(self):
  for child in self.main.winfo_children():child.destroy()
 def heading(self,title,subtitle=''):
  self.label(self.main,'AEGIS  /  OPERATIONS CONSOLE',9,AMBER,True).pack(anchor='w',padx=30,pady=(26,8))
  self.label(self.main,title,26,TEXT,True).pack(anchor='w',padx=30,pady=(0,5))
  self.label(self.main,subtitle,10,MUTED).pack(anchor='w',padx=30,pady=(0,20))
  tk.Frame(self.main,bg=EDGE,height=1).pack(fill='x',padx=30,pady=(0,14))
 def show(self,view):
  self.view=view;self.clear()
  for name,button in self.nav_buttons.items():button.configure(bg='#3a3028' if name==view else '#202c3c',fg=AMBER if name==view else TEXT)
  if view=='Dashboard':self.dashboard()
  elif view=='Machine Registry':self.registry()
  elif view=='Troubleshooting Wizard':self.wizard()
  else:self.knowledge()
 def dashboard(self):
  self.heading('Command overview','Your centralized workspace for machine records, guided diagnosis and documented solutions')
  hero=tk.Frame(self.main,bg='#1b2636',padx=25,pady=23);hero.pack(fill='x',padx=30,pady=(4,19))
  self.label(hero,'ENGINEERING KNOWLEDGE SYSTEM',10,AMBER,True).pack(anchor='w')
  self.label(hero,'Every solution. One workspace.',21,TEXT,True).pack(anchor='w',pady=(7,6))
  self.label(hero,'Offline-capable  •  Shared CSV database  •  26 reference machines',10,MUTED).pack(anchor='w')
  bar=tk.Frame(self.main,bg=BG);bar.pack(fill='x',padx=25,pady=(0,13))
  for title,val,sub in [('MACHINES','26','Registered reference IDs'),('ARTICLES',str(len(self.rows)),'Saved knowledge records'),('DATABASE','ONLINE' if self.path.exists() else 'MISSING','Shared CSV connection')]:
   tile=tk.Frame(bar,bg=PANEL,padx=19,pady=19,highlightbackground=EDGE,highlightthickness=1);tile.pack(side='left',fill='both',expand=True,padx=5)
   self.label(tile,title,9,MUTED,True).pack(anchor='w')
   self.label(tile,val,25,AMBER,True).pack(anchor='w',pady=(8,2))
   self.label(tile,sub,9,MUTED).pack(anchor='w')
  self.label(self.main,'QUICK ACTIONS',11,TEXT,True).pack(anchor='w',padx=30,pady=(20,12))
  for title,view in [('▤   Explore machine registry','Machine Registry'),('◇   Launch troubleshooting wizard','Troubleshooting Wizard'),('▣   Browse knowledge articles','Knowledge Base')]:
   self.btn(self.main,title,lambda v=view:self.show(v)).pack(fill='x',padx=30,pady=5)
  self.label(self.main,'DATABASE PATH  •  '+str(self.path),9,MUTED).pack(anchor='w',padx=30,pady=19)
 def registry(self):
  self.heading('MACHINE REGISTRY','26 reference IDs; status and machine data are not live')
  grid=tk.Frame(self.main,bg=BG);grid.pack(fill='x',padx=25)
  for i in range(26):
   m='AVI-'+str(i+1).zfill(2)
   b=tk.Button(grid,text='▣  '+m,bg=AMBER if m==self.machine else PANEL,fg='#101720' if m==self.machine else TEXT,activebackground='#d58a30',relief='flat',padx=12,pady=15,font=('Segoe UI',10,'bold'),cursor='hand2',command=lambda x=m:self.choose_machine(x))
   b.grid(row=i//7,column=i%7,padx=4,pady=4,sticky='ew')
  self.label(self.main,'Selected: '+self.machine,15,AMBER,True).pack(anchor='w',padx=30,pady=(25,10))
  matches=[r for r in self.rows if r.get('machine','').upper()==self.machine]
  self.label(self.main,f'{len(matches)} saved knowledge record(s) for this machine',11,MUTED).pack(anchor='w',padx=30)
  for r in matches[:10]:self.label(self.main,'• '+r['title'],11).pack(anchor='w',padx=35,pady=3)
  self.btn(self.main,'Add record for '+self.machine,lambda:self.edit_record(machine=self.machine)).pack(anchor='w',padx=30,pady=15)
 def choose_machine(self,m):self.machine=m;self.show('Machine Registry')
 def wizard(self):
  self.heading('GUIDED TROUBLESHOOTING','Document observations and follow site-approved procedures')
  wrap=tk.Frame(self.main,bg=PANEL,padx=24,pady=20);wrap.pack(fill='both',expand=True,padx=30,pady=10)
  self.label(wrap,'Select symptom',12,AMBER,True).pack(anchor='w')
  issue=tk.StringVar(value=list(ISSUES)[0]);combo=ttk.Combobox(wrap,textvariable=issue,values=list(ISSUES),state='readonly',width=42);combo.pack(anchor='w',pady=12)
  self.label(wrap,'Machine ID',11,MUTED).pack(anchor='w')
  machine=tk.StringVar(value=self.machine);ttk.Combobox(wrap,textvariable=machine,values=['AVI-'+str(i).zfill(2) for i in range(1,27)],state='readonly',width=18).pack(anchor='w',pady=8)
  output=tk.Text(wrap,height=14,bg='#0b1523',fg=TEXT,insertbackground=TEXT,wrap='word',relief='flat',font=('Segoe UI',10));output.pack(fill='both',expand=True,pady=12)
  def run():
   output.delete('1.0','end');output.insert('end',f'TROUBLESHOOTING CHECKLIST — {machine.get()}\nSYMPTOM: {issue.get()}\n\n')
   for n,(question,guidance) in enumerate(ISSUES[issue.get()],1):output.insert('end',f'{n}. {question}\n   Guidance: {guidance}\n\n')
   output.insert('end','Record observations and follow authorized escalation procedures.\n')
  self.btn(wrap,'Generate Checklist',run).pack(anchor='w');run()
  def add():
   self.edit_record(machine=machine.get(),title=issue.get(),symptoms=output.get('1.0','end').strip())
  self.btn(wrap,'Save as Knowledge Record',add).pack(anchor='w',pady=6)
 def knowledge(self):
  self.heading('KNOWLEDGE BASE','Search, document and update approved troubleshooting procedures')
  tools=tk.Frame(self.main,bg=BG);tools.pack(fill='x',padx=28,pady=5)
  query=tk.StringVar();entry=tk.Entry(tools,textvariable=query,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',12));entry.pack(side='left',fill='x',expand=True,ipady=10,padx=(0,12))
  self.btn(tools,'+ New Article',lambda:self.edit_record()).pack(side='left')
  tree=ttk.Treeview(self.main,columns=('id','title','machine','category'),show='headings',selectmode='browse')
  for col,w in [('id',75),('title',340),('machine',115),('category',150)]:tree.heading(col,text=col.upper());tree.column(col,width=w,stretch=col=='title')
  tree.pack(fill='both',expand=True,padx=28,pady=16)
  def fill(*_):
   for item in tree.get_children():tree.delete(item)
   q=query.get().lower()
   for idx,r in enumerate(self.rows):
    if q in ' '.join(str(v) for v in r.values()).lower():tree.insert('', 'end',iid=str(idx),values=[r.get(c,'') for c in ('id','title','machine','category')])
  query.trace_add('write',fill);fill()
  def selected():
   s=tree.selection();return int(s[0]) if s else None
  actions=tk.Frame(self.main,bg=BG);actions.pack(fill='x',padx=28,pady=(0,20))
  def edit():
   idx=selected()
   if idx is not None:self.edit_record(index=idx)
  def delete():
   idx=selected()
   if idx is not None and messagebox.askyesno('Delete article','Delete selected record?'):
    self.rows.pop(idx);self.dirty=True;self.show('Knowledge Base')
  self.btn(actions,'Edit Selected',edit).pack(side='left',padx=4)
  self.btn(actions,'Delete Selected',delete).pack(side='left',padx=4)
 def edit_record(self,index=None,machine='',title='',symptoms=''):
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
  else:self.path=DEFAULT;self.rows=[];self.status.config(text='Database missing:\n'+str(DEFAULT));self.show('Dashboard')
 def load(self,path):
  try:
   with open(path,'r',encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    if not set(FIELDS).issubset(reader.fieldnames or []):raise ValueError('CSV headers do not match expected schema')
    self.rows=[{k:r.get(k,'') for k in FIELDS} for r in reader]
   self.path=Path(path);self.dirty=False;self.status.config(text='Connected:\n'+str(self.path));self.show(self.view)
  except Exception as e:messagebox.showerror('CSV load error',str(e))
 def open_csv(self):
  p=filedialog.askopenfilename(filetypes=[('CSV database','*.csv')])
  if p:self.load(p)
 def save(self):
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
  if self.dirty and not messagebox.askyesno('Unsaved edits','Discard unsaved changes?'):return
  self.root.destroy()
if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
