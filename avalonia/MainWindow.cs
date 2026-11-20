using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Interactivity;
using System.Text.Json;
using System.Globalization;

namespace Zentrek;

public sealed class MainWindow : Window
{
    static readonly IBrush Bg = Brush.Parse("#090A0D"), Surface = Brush.Parse("#171A1F"),
        Subtle = Brush.Parse("#252A30"), Text = Brush.Parse("#F4F5F7"),
        Muted = Brush.Parse("#9CA5B0"), Orange = Brush.Parse("#FF922E");
    readonly StackPanel content = new() { Spacing = 16, Margin = new Thickness(32,26) };
    readonly StackPanel menu = new() { Spacing = 6, Margin = new Thickness(16,24) };
    readonly string root = AppContext.BaseDirectory;
    string active = "Dashboard";
    DateTime calendarMonth = new(2026,11,1), selected = new(2026,11,20);
    readonly List<Machine> machines = new();
    readonly List<Article> articles = new();
    readonly List<Pin> pins = new();
    string databaseMessage = "";
    public MainWindow()
    {
        Title = "ZENTREK  /  AVI Knowledge Hub V4.2.5";
        Width=1360;Height=850;MinWidth=1050;MinHeight=680;Background=Bg;
        LoadData();
        var outer = new Grid { ColumnDefinitions = new ColumnDefinitions("255,*") };
        var side = new Border { Background=Brush.Parse("#101216"), Child=menu };
        Grid.SetColumn(side,0);outer.Children.Add(side);
        var scroll = new ScrollViewer { Content=content, HorizontalScrollBarVisibility=ScrollBarVisibility.Disabled };
        Grid.SetColumn(scroll,1);outer.Children.Add(scroll);
        Content=outer;
        RenderMenu();Show("Dashboard");
    }
    static TextBlock T(string value,int size=13,IBrush? color=null,bool bold=false) =>
        new() { Text=value,FontSize=size,Foreground=color??Text,FontWeight=bold?FontWeight.SemiBold:FontWeight.Normal,
            TextWrapping=TextWrapping.Wrap,VerticalAlignment=VerticalAlignment.Center };
    static Border Panel(Control child,int pad=20) => new()
    { Background=Surface,CornerRadius=new CornerRadius(14),Padding=new Thickness(pad),Child=child };
    static Button B(string title,Action action,bool accent=false)
    {
        var b=new Button { Content=title,Padding=new Thickness(15,11),HorizontalAlignment=HorizontalAlignment.Stretch,
            Background=accent?Orange:Subtle,Foreground=accent?Brushes.Black:Text,
            BorderThickness=new Thickness(0),CornerRadius=new CornerRadius(9),HorizontalContentAlignment=HorizontalAlignment.Center };
        b.Click+=(_,_)=>action();return b;
    }
    void RenderMenu()
    {
        menu.Children.Clear();
        menu.Children.Add(T("◆  ZENTREK",28,Text,true));
        menu.Children.Add(T("AVI OPERATIONS   /   V4.2.5",10,Orange,true));
        menu.Children.Add(new Border { Height=30 });
        menu.Children.Add(T("WORKSPACE",10,Muted,true));
        foreach(var page in new[]{"Dashboard","Machine Registry","Troubleshooting","Knowledge Base","Shift Calendar"})
        {
            var p=page;
            var b=B("   "+page,()=>Show(p));
            b.HorizontalContentAlignment=HorizontalAlignment.Left;
            b.Background=page==active?Brush.Parse("#33271D"):Brushes.Transparent;
            b.Foreground=page==active?Orange:Text;
            menu.Children.Add(b);
        }
        menu.Children.Add(new Border { Height=25 });
        menu.Children.Add(T("DATABASE",10,Muted,true));
        menu.Children.Add(B("↻   Reload shared files",()=>{LoadData();Show(active);}));
        menu.Children.Add(T(databaseMessage,11,Muted));
        menu.Children.Add(new Border { Height=15 });
        menu.Children.Add(T("Read-only migration preview. The Python V4.2.4 app remains available for editing.",11,Muted));
    }
    void Show(string page)
    {
        active=page;RenderMenu();content.Children.Clear();
        content.Children.Add(T("ZENTREK   /   PRODUCTION OPERATIONS",11,Orange,true));
        content.Children.Add(T(page=="Dashboard"?"Operations overview":page,30,Text,true));
        content.Children.Add(T(page=="Dashboard"?"Machine registry, knowledge and shift operations": "Premium native Windows workspace",13,Muted));
        content.Children.Add(new Border { Height=1,Background=Subtle,Margin=new Thickness(0,5,0,6) });
        switch(page)
        {
            case "Dashboard":Dashboard();break;
            case "Machine Registry":Registry();break;
            case "Troubleshooting":Troubleshooting();break;
            case "Knowledge Base":Knowledge();break;
            case "Shift Calendar":Calendar();break;
        }
    }
    void Dashboard()
    {
        var metrics=new Grid { ColumnDefinitions=new ColumnDefinitions("*,*,*,*"),ColumnSpacing=12 };
        var entries=new[]{("MACHINES",machines.Count.ToString()),("KNOWLEDGE ARTICLES",articles.Count.ToString()),("PINNED NOTES",pins.Count.ToString()),("DATA SOURCE",File.Exists(Path.Combine(root,"Database","AVI_Database.csv"))?"CONNECTED":"MISSING")};
        for(int i=0;i<entries.Length;i++)
        {
            var stack=new StackPanel{Spacing=8};
            stack.Children.Add(T(entries[i].Item1,11,Muted,true));
            stack.Children.Add(T(entries[i].Item2,25,i==3?Orange:Text,true));
            var tile=Panel(stack,23);Grid.SetColumn(tile,i);metrics.Children.Add(tile);
        }
        content.Children.Add(metrics);
        content.Children.Add(T("IMMEDIATE ATTENTION  /  PINBOARD",15,Orange,true));
        if(pins.Count==0)content.Children.Add(Panel(T("No saved pinboard notes.",13,Muted)));
        foreach(var pin in pins.Take(12))
        {
            var p=new StackPanel{Spacing=7};p.Children.Add(T(pin.Title,15,Text,true));p.Children.Add(T(pin.Body,12,Muted));
            content.Children.Add(Panel(p));
        }
        content.Children.Add(T("Machine statuses and notes are manually maintained; this is not live monitoring.",11,Muted));
    }
    void Registry()
    {
        content.Children.Add(T("26-MACHINE REGISTRY   /   EXISTING FLOORPLAN POSITIONS",12,Orange,true));
        var wrap=new WrapPanel { Orientation=Orientation.Horizontal,ItemWidth=175,ItemHeight=100 };
        foreach(var m in machines)
        {
            var card=new StackPanel{Spacing=7,Margin=new Thickness(6)};
            card.Children.Add(T(m.Name,15,Text,true));
            card.Children.Add(T(m.Id,11,Muted));
            card.Children.Add(T("●  "+m.Status,12,m.Status=="Down"?Brush.Parse("#FF6677"):Orange));
            var tile=Panel(card,13);
            tile.Width=160;tile.Height=89;wrap.Children.Add(tile);
        }
        content.Children.Add(wrap);
        content.Children.Add(T("Registry is currently read-only in Avalonia. Existing JSON coordinates and machine details are preserved, not overwritten.",12,Muted));
    }
    void Knowledge()
    {
        var search=new TextBox{Watermark="Search ID, title, machine, symptoms or solution",FontSize=14,Padding=new Thickness(14)};
        var results=new StackPanel{Spacing=9};
        content.Children.Add(search);content.Children.Add(results);
        void Render()
        {
            results.Children.Clear();
            var q=search.Text??"";
            var hits=articles.Where(a=>string.IsNullOrWhiteSpace(q)||a.Fields.Values.Any(v=>v.Contains(q,StringComparison.OrdinalIgnoreCase))).Take(80).ToList();
            results.Children.Add(T($"{hits.Count} visible records",12,Muted));
            foreach(var a in hits)
            {
                var stack=new StackPanel{Spacing=7};
                stack.Children.Add(T(a.Get("title"),16,Text,true));
                stack.Children.Add(T($"{a.Get("id")}   •   {a.Get("machine")}   •   {a.Get("category")}",11,Orange));
                stack.Children.Add(T("SYMPTOMS   "+a.Get("symptoms"),12,Muted));
                stack.Children.Add(T("SOLUTION   "+a.Get("solution"),12,Text));
                results.Children.Add(Panel(stack));
            }
        }
        search.PropertyChanged+=(_,e)=>{if(e.Property.Name=="Text")Render();};
        Render();
    }
    void Troubleshooting()
    {
        content.Children.Add(Panel(T("Search approved knowledge articles by symptom or machine. This Avalonia preview does not yet reproduce the Python interactive decision-tree wizard.",13,Muted)));
        var field=new TextBox{Watermark="Enter symptom or machine ID",Padding=new Thickness(14)};
        var results=new StackPanel{Spacing=10};content.Children.Add(field);content.Children.Add(results);
        void Render()
        {
            results.Children.Clear();
            var q=field.Text?.Trim()??"";
            if(q.Length<2){results.Children.Add(T("Type at least two characters to find relevant guidance.",12,Muted));return;}
            foreach(var a in articles.Where(a=>a.Fields.Values.Any(v=>v.Contains(q,StringComparison.OrdinalIgnoreCase))).Take(20))
            {
                var panel=new StackPanel{Spacing=5};
                panel.Children.Add(T(a.Get("title"),16,Orange,true));
                panel.Children.Add(T(a.Get("symptoms"),12,Muted));
                panel.Children.Add(T(a.Get("solution"),12,Text));
                results.Children.Add(Panel(panel));
            }
        }
        field.PropertyChanged+=(_,e)=>{if(e.Property.Name=="Text")Render();};Render();
    }
    static (string morn,string night,string off) Assignment(DateTime day)
    {
        if(day.Year!=2026)return ("—","—","—");
        if(day.DayOfWeek==DayOfWeek.Sunday)return ("RD","RD","RD");
        var cycle=new[]{new[]{(1,2,3),(3,2,1),(3,1,2)},new[]{(2,3,1),(1,3,2),(1,2,3)},new[]{(3,1,2),(2,1,3),(2,3,1)}};
        int week=(int)Math.Floor((day-new DateTime(2026,4,6)).TotalDays/7.0);
        int group=((week%3)+3)%3;
        var shift=cycle[group][((int)day.DayOfWeek+6)%7/2];
        return (shift.Item1.ToString(),shift.Item2.ToString(),shift.Item3.ToString());
    }
    void Calendar()
    {
        var nav=new StackPanel{Orientation=Orientation.Horizontal,Spacing=12};
        nav.Children.Add(B("‹ Previous",()=>{calendarMonth=calendarMonth.AddMonths(-1);Show("Shift Calendar");}));
        nav.Children.Add(T(calendarMonth.ToString("MMMM yyyy",CultureInfo.InvariantCulture),20,Text,true));
        nav.Children.Add(B("Next ›",()=>{calendarMonth=calendarMonth.AddMonths(1);Show("Shift Calendar");}));
        nav.Children.Add(B("Today",()=>{selected=DateTime.Today;calendarMonth=new DateTime(selected.Year,selected.Month,1);Show("Shift Calendar");}));
        content.Children.Add(nav);
        var a=Assignment(selected);
        content.Children.Add(Panel(new StackPanel{Spacing=8,Children={
            T(selected.ToString("dddd, dd MMMM yyyy"),17,Orange,true),
            T(a.morn=="RD"?"REST DAY  /  ALL GROUPS":$"MORNING   {a.morn}       NIGHT   {a.night}       OFF   {a.off}",16,Text,true)
        }}));
        var days=new Grid{ColumnDefinitions=new ColumnDefinitions("*,*,*,*,*,*,*"),RowDefinitions=new RowDefinitions("Auto,Auto,Auto,Auto,Auto,Auto,Auto"),ColumnSpacing=6,RowSpacing=6};
        string[] labels={"MON","TUE","WED","THU","FRI","SAT","SUN"};
        for(int c=0;c<7;c++){var h=T(labels[c],11,Muted,true);Grid.SetColumn(h,c);Grid.SetRow(h,0);days.Children.Add(h);}
        int offset=((int)calendarMonth.DayOfWeek+6)%7;
        for(int n=0;n<42;n++)
        {
            var d=calendarMonth.AddDays(n-offset);
            var shift=Assignment(d);
            var text=shift.morn=="RD"?"RD  ALL":shift.morn=="—"?"No roster":$"M {shift.morn}  N {shift.night}\nOFF {shift.off}";
            var btn=B($"{d.Day}\n{text}",()=>{selected=d;calendarMonth=new DateTime(d.Year,d.Month,1);Show("Shift Calendar");});
            btn.MinHeight=74;btn.FontSize=12;
            btn.Background=d.Date==selected.Date?Brush.Parse("#46301F"):d.Month==calendarMonth.Month?Surface:Brush.Parse("#111317");
            btn.Foreground=d.Month==calendarMonth.Month?Text:Muted;
            Grid.SetColumn(btn,n%7);Grid.SetRow(btn,n/7+1);days.Children.Add(btn);
        }
        content.Children.Add(days);
        content.Children.Add(T("2026 roster is based on the previous Python V4.2.4 rotation and still requires verification against the original shift cards.",11,Muted));
    }
    void LoadData()
    {
        machines.Clear();articles.Clear();pins.Clear();
        for(int i=1;i<=26;i++)machines.Add(new Machine($"AVI-{i:00}",$"AVI {i:00}","Idle"));
        var db=Path.Combine(root,"Database");
        try
        {
            var file=Path.Combine(db,"ZENTREK_Floorplan.json");
            if(File.Exists(file))
            {
                using var doc=JsonDocument.Parse(File.ReadAllText(file));
                var data=doc.RootElement;
                if(data.TryGetProperty("machines",out var list)&&list.ValueKind==JsonValueKind.Array)
                {
                    machines.Clear();
                    foreach(var m in list.EnumerateArray())
                    {
                        string Get(string key,string fallback="")=>m.TryGetProperty(key,out var v)?v.ToString():fallback;
                        machines.Add(new Machine(Get("id"),Get("name",Get("id")),Get("status","Idle")));
                    }
                }
                if(data.TryGetProperty("notes",out var notes)&&notes.ValueKind==JsonValueKind.Array)
                    foreach(var n in notes.EnumerateArray())
                    {
                        string Get(string key)=>n.TryGetProperty(key,out var v)?v.ToString():"";
                        pins.Add(new Pin(Get("title"),Get("body")));
                    }
            }
        }
        catch(Exception ex){databaseMessage="Floorplan warning: "+ex.Message;}
        try
        {
            var csv=Path.Combine(db,"AVI_Database.csv");
            if(File.Exists(csv))
            {
                var lines=File.ReadAllLines(csv);
                if(lines.Length>0)
                {
                    var heads=CsvLine(lines[0]).Select(x=>x.Trim('\uFEFF')).ToArray();
                    foreach(var line in lines.Skip(1))
                    {
                        if(string.IsNullOrWhiteSpace(line))continue;
                        var values=CsvLine(line);
                        var fields=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
                        for(int i=0;i<heads.Length;i++)fields[heads[i]]=i<values.Count?values[i]:"";
                        articles.Add(new Article(fields));
                    }
                }
                databaseMessage="Connected: Database/AVI_Database.csv";
            }
            else databaseMessage="CSV not found. Place the approved database beside the EXE.";
        }
        catch(Exception ex){databaseMessage="CSV read warning: "+ex.Message;}
    }
    static List<string> CsvLine(string line)
    {
        var fields=new List<string>();var part=new System.Text.StringBuilder();bool quoted=false;
        for(int i=0;i<line.Length;i++)
        {
            char c=line[i];
            if(c=='"'){if(quoted&&i+1<line.Length&&line[i+1]=='"'){part.Append('"');i++;}else quoted=!quoted;}
            else if(c==','&&!quoted){fields.Add(part.ToString());part.Clear();}
            else part.Append(c);
        }
        fields.Add(part.ToString());return fields;
    }
    sealed record Machine(string Id,string Name,string Status);
    sealed record Pin(string Title,string Body);
    sealed record Article(Dictionary<string,string> Fields)
    {
        public string Get(string key)=>Fields.TryGetValue(key,out var value)?value:"";
    }
}