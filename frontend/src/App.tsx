import { FormEvent, useEffect, useRef, useState } from "react";
import { Heart, Brain, MessageCircle, Plus, ShieldCheck, Sparkles, Send, ArrowLeft, Settings, Trash2, Pencil, Clock3, CalendarHeart } from "lucide-react";


type SpeechRecognitionAlternativeLike = { transcript:string };
type SpeechRecognitionResultLike = { 0:SpeechRecognitionAlternativeLike; isFinal:boolean };
type SpeechRecognitionEventLike = { resultIndex:number; results:ArrayLike<SpeechRecognitionResultLike> };
type SpeechRecognitionErrorLike = { error:string };
type SpeechRecognitionLike = {
  lang:string; continuous:boolean; interimResults:boolean;
  onresult:((event:SpeechRecognitionEventLike)=>void)|null;
  onerror:((event:SpeechRecognitionErrorLike)=>void)|null;
  onend:(()=>void)|null;
  start:()=>void; stop:()=>void; abort:()=>void;
};
declare global {
  interface Window {
    SpeechRecognition?:new()=>SpeechRecognitionLike;
    webkitSpeechRecognition?:new()=>SpeechRecognitionLike;
  }
}

type PersonalityConfig = { preset:"custom"|"gentle"|"playful"|"romantic"|"serious"; humor:number; warmth:number; seriousness:number; expressiveness:number; voice_style:string; backstory:string };
type Companion = { id:string; name:string; age:number; short_description:string; personality_prompt:string; traits:string[]; interests:string[]; personality_config:PersonalityConfig; avatar_url?:string|null };
type Session = { id:string; companion_id:string; title:string; created_at?:string };
type Message = { id:string; role:string; content:string };
type Memory = { id:string; category:string; content:string; importance:number };
type Candidate = { category:string; content:string; importance:number };
type EmotionalState = { mood:string; closeness:number; trust:number; energy:number; interaction_count:number };
type TimelineEvent = { id:string; title:string; description:string; event_type:string; occurred_at:string };

async function api<T>(path:string, options:RequestInit={}):Promise<T>{
  const response=await fetch(path,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"درخواست ناموفق بود.");}
  if(response.status===204) return undefined as T;
  return response.json();
}

export default function App(){
  const [companions,setCompanions]=useState<Companion[]>([]);
  const [selected,setSelected]=useState<Companion|null>(null);
  const [session,setSession]=useState<Session|null>(null);
  const [messages,setMessages]=useState<Message[]>([]);
  const [sessions,setSessions]=useState<Session[]>([]);
  const [draft,setDraft]=useState("");
  const [view,setView]=useState<"home"|"create"|"chat"|"settings"|"memory"|"edit"|"timeline">("home");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [health,setHealth]=useState(false);
  const [provider,setProvider]=useState<{configured:boolean;model:string}|null>(null);
  const [memories,setMemories]=useState<Memory[]>([]);
  const [candidates,setCandidates]=useState<Candidate[]>([]);
  const [emotionalState,setEmotionalState]=useState<EmotionalState|null>(null);
  const [timelineEvents,setTimelineEvents]=useState<TimelineEvent[]>([]);
  const [eventForm,setEventForm]=useState({title:"",description:"",event_type:"memory"});
  const [form,setForm]=useState({name:"",age:24,short_description:"",personality_prompt:"",traits:"مهربان، شوخ‌طبع",interests:"موسیقی، فیلم، سفر",avatar_url:""});
  const [editingId,setEditingId]=useState<string|null>(null);
  const defaultPersonality:PersonalityConfig={preset:"custom",humor:55,warmth:70,seriousness:35,expressiveness:65,voice_style:"صمیمی و طبیعی",backstory:""};
  const [personality,setPersonality]=useState<PersonalityConfig>(defaultPersonality);
  const [speechRate,setSpeechRate]=useState(1);
  const [speechPitch,setSpeechPitch]=useState(1);
  const [speaking,setSpeaking]=useState(false);
  const [listening,setListening]=useState(false);
  const [autoSpeak,setAutoSpeak]=useState(false);
  const recognitionRef=useRef<SpeechRecognitionLike|null>(null);
  const applyPreset=(preset:PersonalityConfig["preset"])=>{
    const presets:Record<PersonalityConfig["preset"],PersonalityConfig>={
      custom:{...personality,preset:"custom"},
      gentle:{...personality,preset:"gentle",humor:25,warmth:92,seriousness:55,expressiveness:55,voice_style:"آرام، مهربان و شنونده"},
      playful:{...personality,preset:"playful",humor:90,warmth:78,seriousness:18,expressiveness:92,voice_style:"شوخ، پرانرژی و خودمانی"},
      romantic:{...personality,preset:"romantic",humor:55,warmth:95,seriousness:30,expressiveness:85,voice_style:"لطیف، صمیمی و رمانتیک"},
      serious:{...personality,preset:"serious",humor:12,warmth:48,seriousness:92,expressiveness:35,voice_style:"آرام، دقیق و جدی"}
    };
    setPersonality(presets[preset]);
  };
  const avatarField=<label className="wide">نشانی تصویر شخصیت<input type="url" maxLength={1000} value={form.avatar_url} onChange={e=>setForm({...form,avatar_url:e.target.value})} placeholder="https://example.com/avatar.jpg"/></label>;
  const personalityStudio=<div className="personality-studio wide"><div className="studio-heading"><Sparkles size={16}/> Personality Studio</div><label>قالب اولیه شخصیت<select value={personality.preset} onChange={e=>applyPreset(e.target.value as PersonalityConfig["preset"])}><option value="custom">شخصی‌سازی‌شده</option><option value="gentle">آرام و مهربان</option><option value="playful">شوخ و پرانرژی</option><option value="romantic">رمانتیک</option><option value="serious">جدی و متین</option></select></label><div className="personality-sliders">{([{key:"humor",label:"شوخ‌طبعی"},{key:"warmth",label:"صمیمیت"},{key:"seriousness",label:"جدیت"},{key:"expressiveness",label:"ابراز احساسات"}] as const).map(item=><label className="personality-range" key={item.key}><span>{item.label}<b>{personality[item.key]}%</b></span><input type="range" min="0" max="100" value={personality[item.key]} onChange={e=>setPersonality({...personality,[item.key]:Number(e.target.value),preset:"custom"})}/></label>)}</div><label>سبک صحبت<input maxLength={120} value={personality.voice_style} onChange={e=>setPersonality({...personality,voice_style:e.target.value,preset:"custom"})} placeholder="مثلاً صمیمی، کوتاه و شوخ"/></label><label>گذشته و پیش‌زمینه داستانی<textarea rows={3} maxLength={4000} value={personality.backstory} onChange={e=>setPersonality({...personality,backstory:e.target.value})} placeholder="گذشته و جزئیات داستانی شخصیت را اینجا تعریف کن…"/></label></div>;
  const speakText=(text:string)=>{
    if(!("speechSynthesis" in window)){setError("مرورگر شما از پخش گفتار پشتیبانی نمی‌کند.");return;}
    window.speechSynthesis.cancel();
    const utterance=new SpeechSynthesisUtterance(text);
    utterance.lang="fa-IR";utterance.rate=speechRate;utterance.pitch=speechPitch;
    const voices=window.speechSynthesis.getVoices();
    const persianVoice=voices.find(v=>v.lang.toLowerCase().startsWith("fa"));
    if(persianVoice)utterance.voice=persianVoice;
    utterance.onstart=()=>setSpeaking(true);
    utterance.onend=()=>setSpeaking(false);
    utterance.onerror=()=>setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };
  const stopSpeaking=()=>{if("speechSynthesis" in window)window.speechSynthesis.cancel();setSpeaking(false);};
  const startListening=()=>{
    const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!Recognition){setError("تشخیص گفتار در این مرورگر در دسترس نیست. از نسخه به‌روز Edge یا Chrome استفاده کن.");return;}
    if(listening){recognitionRef.current?.stop();setListening(false);return;}
    stopSpeaking();
    const recognition=new Recognition();
    recognition.lang="fa-IR";recognition.continuous=false;recognition.interimResults=false;
    recognition.onresult=(event)=>{
      const transcripts:string[]=[];
      for(let i=event.resultIndex;i<event.results.length;i++){
        if(event.results[i].isFinal)transcripts.push(event.results[i][0].transcript);
      }
      const transcript=transcripts.join(" ").trim();
      if(transcript)setDraft(current=>current?current+" "+transcript:transcript);
    };
    recognition.onerror=(event)=>{setListening(false);if(event.error!=="no-speech"&&event.error!=="aborted")setError("خطا در دریافت صدا: "+event.error);};
    recognition.onend=()=>setListening(false);
    recognitionRef.current=recognition;
    setError("");setListening(true);
    try{recognition.start();}catch{setListening(false);setError("شروع میکروفون ممکن نشد. مجوز میکروفون مرورگر را بررسی کن.");}
  };

  const load=async()=>{try{const [list,h,p]=await Promise.all([api<Companion[]>("/api/companions"),api<{status:string}>("/api/health"),api<{configured:boolean;model:string}>("/api/settings/provider")]);setCompanions(list);setSelected(current=>current??list[0]??null);if(list.length){api<Session[]>(`/api/companions/${list[0].id}/sessions`).then(setSessions).catch(()=>setSessions([]));}setHealth(h.status==="ok");setProvider(p);}catch{setHealth(false);}};
  useEffect(()=>{load();},[]);
  const editCompanion=(c:Companion)=>{setEditingId(c.id);setForm({name:c.name,age:c.age,short_description:c.short_description,personality_prompt:c.personality_prompt,traits:c.traits.join("، "),interests:c.interests.join("، "),avatar_url:c.avatar_url||""});setPersonality(c.personality_config||defaultPersonality);setView("edit");setError("");};
  const updateCompanion=async(e:FormEvent)=>{e.preventDefault();if(!editingId)return;setBusy(true);setError("");try{const updated=await api<Companion>(`/api/companions/${editingId}`,{method:"PATCH",body:JSON.stringify({...form,personality_config:personality,traits:form.traits.split(/[،,]/).map(x=>x.trim()).filter(Boolean),interests:form.interests.split(/[،,]/).map(x=>x.trim()).filter(Boolean)})});setCompanions(v=>v.map(c=>c.id===updated.id?updated:c));setSelected(updated);setView("home");setEditingId(null);}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const createCompanion=async(e:FormEvent)=>{e.preventDefault();setBusy(true);setError("");try{const c=await api<Companion>("/api/companions",{method:"POST",body:JSON.stringify({...form,personality_config:personality,traits:form.traits.split(/[،,]/).map(x=>x.trim()).filter(Boolean),interests:form.interests.split(/[،,]/).map(x=>x.trim()).filter(Boolean)})});setCompanions(v=>[c,...v]);setSelected(c);setView("home");setForm({name:"",age:24,short_description:"",personality_prompt:"",traits:"مهربان، شوخ‌طبع",interests:"موسیقی، فیلم، سفر",avatar_url:""});setPersonality(defaultPersonality);}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const openChat=async(c:Companion)=>{setBusy(true);setError("");try{const s=await api<Session>(`/api/companions/${c.id}/sessions`,{method:"POST"});setSelected(c);setSession(s);setMessages([]);const state=await api<EmotionalState>(`/api/companions/${c.id}/emotional-state`);setEmotionalState(state);await loadSessions(c);setView("chat");}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const loadSessions=async(c:Companion)=>{try{setSessions(await api<Session[]>(`/api/companions/${c.id}/sessions`));}catch(e){setError((e as Error).message);}};
  const resumeChat=async(c:Companion,s:Session)=>{setBusy(true);setError("");try{const history=await api<Message[]>(`/api/sessions/${s.id}/messages`);setSelected(c);setSession(s);setMessages(history);setView("chat");}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const loadTimeline=async(c:Companion)=>{setSelected(c);setError("");try{setTimelineEvents(await api<TimelineEvent[]>(`/api/companions/${c.id}/timeline`));setView("timeline");}catch(e){setError((e as Error).message);}};
  const addTimelineEvent=async(e:FormEvent)=>{e.preventDefault();if(!selected)return;setBusy(true);setError("");try{const saved=await api<TimelineEvent>(`/api/companions/${selected.id}/timeline`,{method:"POST",body:JSON.stringify(eventForm)});setTimelineEvents(v=>[saved,...v]);setEventForm({title:"",description:"",event_type:"memory"});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const deleteTimelineEvent=async(id:string)=>{if(!selected)return;try{await api(`/api/companions/${selected.id}/timeline/${id}`,{method:"DELETE"});setTimelineEvents(v=>v.filter(item=>item.id!==id));}catch(e){setError((e as Error).message);}};
  const loadMemories=async(c:Companion)=>{setSelected(c);setError("");try{setMemories(await api<Memory[]>(`/api/companions/${c.id}/memories`));setView("memory");}catch(e){setError((e as Error).message);}};
  const saveMemory=async(item:Candidate)=>{if(!selected)return;try{const saved=await api<Memory>(`/api/companions/${selected.id}/memories`,{method:"POST",body:JSON.stringify(item)});setMemories(v=>[saved,...v]);setCandidates(v=>v.filter(x=>x!==item));}catch(e){setError((e as Error).message);}};
  const suggestMemories=async()=>{if(!session)return;setBusy(true);setError("");try{setCandidates(await api<Candidate[]>(`/api/sessions/${session.id}/memory-suggestions`,{method:"POST"}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const deleteMemory=async(id:string)=>{if(!selected)return;try{await api(`/api/companions/${selected.id}/memories/${id}`,{method:"DELETE"});setMemories(v=>v.filter(x=>x.id!==id));}catch(e){setError((e as Error).message);}};
  const send=async(e:FormEvent)=>{e.preventDefault();if(!draft.trim()||!session)return;const content=draft.trim();setDraft("");setMessages(v=>[...v,{id:crypto.randomUUID(),role:"user",content}]);setBusy(true);setError("");try{const m=await api<Message>(`/api/sessions/${session.id}/messages`,{method:"POST",body:JSON.stringify({content})});setMessages(v=>[...v,m]);if(autoSpeak)speakText(m.content);if(selected){api<EmotionalState>(`/api/companions/${selected.id}/emotional-state`).then(setEmotionalState).catch(()=>{});}}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const remove=async(c:Companion)=>{if(!confirm(`شخصیت «${c.name}» و مکالماتش حذف شود؟`))return;try{await api(`/api/companions/${c.id}`,{method:"DELETE"});setCompanions(v=>v.filter(x=>x.id!==c.id));}catch(e){setError((e as Error).message);}};
  return <main className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Heart size={19} fill="currentColor"/></span><span>NAZI <b>AI</b></span></div><div className="side-label">فضای شخصی</div>
      <button className={view==="home"?"nav-item active":"nav-item"} onClick={()=>setView("home")}><MessageCircle size={17}/> داشبورد</button>
      <button className="nav-item" onClick={()=>setView("create")}><Heart size={17}/> ساخت شخصیت</button>
      <button className="nav-item" onClick={()=>setView("settings")}><Settings size={17}/> تنظیمات API</button>
      <div className="side-bottom"><div className="privacy"><ShieldCheck size={17}/><span><b>فضای خصوصی</b><small>اجرا روی همین دستگاه</small></span></div><div className="version">NAZI AI · LOCAL BUILD 0.2</div></div>
    </aside>
    <section className="main-panel"><header className="topbar"><span>دستیار هوشمند شخصی</span><div className="local-pill"><i/> LOCAL MODE</div></header>
    <div className="content">
      {view==="chat"&&selected&&session?<><button className="back-button" onClick={()=>setView("home")}><ArrowLeft size={16}/> بازگشت</button><div className="chat-heading"><div className="avatar">{selected.avatar_url?<img src={selected.avatar_url} alt={selected.name}/>:selected.name.slice(0,1)}</div><div><h2>{selected.name}</h2><p>{selected.short_description||"همراه هوشمند تو"}</p></div></div>{emotionalState&&<div className="state-strip"><span>حال‌وهوای داستانی: {emotionalState.mood==="warm"?"صمیمی":emotionalState.mood==="concerned"?"نگران":"آرام"}</span><span>آشنایی {emotionalState.closeness}%</span><span>انرژی {emotionalState.energy}%</span></div>}<div className="messages">{messages.length===0&&<div className="empty-chat"><Heart size={24}/><p>گفت‌وگو با {selected.name} را شروع کن.</p></div>}{messages.map(m=><div key={m.id} className={m.role==="user"?"bubble user":"bubble assistant"}>{m.content}{m.role==="assistant"&&<button className="speak-button" type="button" onClick={()=>speakText(m.content)} title="خواندن پاسخ با صدا">▶ پخش صدا</button>}</div>)}{busy&&<div className="typing">در حال فکر کردن…</div>}</div><div className="chat-tools"><button className="secondary" type="button" onClick={startListening} disabled={busy} aria-pressed={listening}>{listening?"توقف ضبط":"🎙 صحبت کن"}</button><label className="speech-auto"><input type="checkbox" checked={autoSpeak} onChange={e=>setAutoSpeak(e.target.checked)}/> خواندن خودکار پاسخ‌ها</label><button className="secondary" type="button" onClick={suggestMemories} disabled={busy}>پیشنهاد خاطرات از این گفت‌وگو</button><button className="secondary" type="button" onClick={stopSpeaking} disabled={!speaking}>توقف صدا</button><label className="speech-control">سرعت صدا <input type="range" min="0.7" max="1.3" step="0.1" value={speechRate} onChange={e=>setSpeechRate(Number(e.target.value))}/></label><label className="speech-control">زیر و بمی <input type="range" min="0.7" max="1.3" step="0.1" value={speechPitch} onChange={e=>setSpeechPitch(Number(e.target.value))}/></label></div>{candidates.length>0&&<div className="memory-suggestions"><b>خاطرات پیشنهادی؛ برای ذخیره تأیید کن</b>{candidates.map((item,i)=><div className="memory-row" key={i}><span>{item.content}</span><button className="primary" type="button" onClick={()=>saveMemory(item)}>ذخیره</button></div>)}</div>}<form className="composer" onSubmit={send}><input value={draft} onChange={e=>setDraft(e.target.value)} placeholder="پیامت را بنویس…" disabled={busy}/><button disabled={busy||!draft.trim()}><Send size={17}/></button></form></>:null}
      {view==="edit"&&<><div className="eyebrow"><Pencil size={14}/> CHARACTER EDITOR</div><h1>شخصیت را<br/><em>بازطراحی کن.</em></h1><p className="intro">تغییرات در شخصیت ذخیره می‌شوند و در گفت‌وگوهای بعدی اعمال خواهند شد.</p><form className="creator-form" onSubmit={updateCompanion}><label>نام شخصیت<input required maxLength={80} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>سن (۱۸ سال به بالا)<input type="number" min="18" max="99" value={form.age} onChange={e=>setForm({...form,age:Number(e.target.value)})}/></label><label>توضیح کوتاه<input value={form.short_description} onChange={e=>setForm({...form,short_description:e.target.value})}/></label><label>ویژگی‌های شخصیتی<input value={form.traits} onChange={e=>setForm({...form,traits:e.target.value})}/></label><label>علایق<input value={form.interests} onChange={e=>setForm({...form,interests:e.target.value})}/></label>{avatarField}{form.avatar_url&&<div className="avatar-preview wide"><img src={form.avatar_url} alt="پیش‌نمایش تصویر شخصیت" onError={e=>{e.currentTarget.style.display="none";}}/><span>پیش‌نمایش تصویر شخصیت</span></div>}{personalityStudio}<label className="wide">پرامپت و داستان شخصیت<textarea rows={7} value={form.personality_prompt} onChange={e=>setForm({...form,personality_prompt:e.target.value})}/></label><div className="form-actions"><button className="primary" disabled={busy}><Pencil size={16}/>{busy?"در حال ذخیره…":"ذخیره تغییرات"}</button><button type="button" className="secondary" onClick={()=>setView("home")}>انصراف</button></div></form></>}
      {view==="create"&&<><div className="eyebrow"><Sparkles size={14}/> CHARACTER STUDIO</div><h1>شخصیت دلخواهت را<br/><em>خلق کن.</em></h1><p className="intro">یک شخصیت داستانی بزرگسال با هویت و لحن اختصاصی بساز.</p><form className="creator-form" onSubmit={createCompanion}><label>نام شخصیت<input required maxLength={80} value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="مثلاً نازنین"/></label><label>سن (۱۸ سال به بالا)<input type="number" min="18" max="99" value={form.age} onChange={e=>setForm({...form,age:Number(e.target.value)})}/></label><label>توضیح کوتاه<input value={form.short_description} onChange={e=>setForm({...form,short_description:e.target.value})} placeholder="مثلاً پرانرژی و اهل موسیقی"/></label><label>ویژگی‌های شخصیتی<input value={form.traits} onChange={e=>setForm({...form,traits:e.target.value})}/></label><label>علایق<input value={form.interests} onChange={e=>setForm({...form,interests:e.target.value})}/></label>{avatarField}{form.avatar_url&&<div className="avatar-preview wide"><img src={form.avatar_url} alt="پیش‌نمایش تصویر شخصیت" onError={e=>{e.currentTarget.style.display="none";}}/><span>پیش‌نمایش تصویر شخصیت</span></div>}{personalityStudio}<label className="wide">پرامپت و داستان شخصیت<textarea rows={5} value={form.personality_prompt} onChange={e=>setForm({...form,personality_prompt:e.target.value})} placeholder="درباره اخلاقیات، شیوه صحبت، گذشته داستانی و علایقش توضیح بده…"/></label><div className="form-actions"><button className="primary" disabled={busy}><Plus size={16}/> {busy?"در حال ساخت…":"ساخت شخصیت"}</button><button type="button" className="secondary" onClick={()=>setView("home")}>انصراف</button></div></form></>}
      {view==="timeline"&&selected&&<><div className="eyebrow"><CalendarHeart size={14}/> RELATIONSHIP TIMELINE</div><h1>داستان مشترک<br/><em>{selected.name}</em></h1><p className="intro">اتفاقات مهمی که می‌خواهی این شخصیت در داستان مشترکتان به یاد داشته باشد.</p><form className="timeline-form" onSubmit={addTimelineEvent}><label>عنوان اتفاق<input required maxLength={120} value={eventForm.title} onChange={e=>setEventForm({...eventForm,title:e.target.value})} placeholder="مثلاً اولین گفت‌وگوی طولانی"/></label><label>نوع اتفاق<select value={eventForm.event_type} onChange={e=>setEventForm({...eventForm,event_type:e.target.value})}><option value="memory">خاطره</option><option value="milestone">نقطه عطف</option><option value="first_time">اولین تجربه</option><option value="shared_interest">علاقه مشترک</option><option value="custom">سایر</option></select></label><label className="wide">توضیحات<textarea rows={3} maxLength={2000} value={eventForm.description} onChange={e=>setEventForm({...eventForm,description:e.target.value})} placeholder="جزئیات این اتفاق را بنویس…"/></label><button className="primary" disabled={busy}><Plus size={15}/> ثبت در خط زمانی</button></form>{timelineEvents.length===0?<div className="empty-state">هنوز اتفاقی ثبت نشده است. اولین خاطره را خودت اضافه کن.</div>:<div className="timeline-list">{timelineEvents.map(item=><article className="timeline-event" key={item.id}><div className="timeline-marker"><Clock3 size={15}/></div><div className="timeline-event-body"><span className="memory-category">{item.event_type} · {new Date(item.occurred_at).toLocaleDateString("fa-IR")}</span><h3>{item.title}</h3>{item.description&&<p>{item.description}</p>}</div><button className="icon-button" title="حذف رویداد" onClick={()=>deleteTimelineEvent(item.id)}><Trash2 size={15}/></button></article>)}</div>}</>}
      {view==="memory"&&selected&&<><div className="eyebrow"><Brain size={14}/> MEMORY VAULT</div><h1>خاطرات {selected.name}</h1><p className="intro">خاطرات ذخیره‌شده فقط به همین شخصیت تعلق دارند. می‌توانی آن‌ها را حذف کنی.</p>{memories.length===0?<div className="empty-state">هنوز خاطره‌ای ذخیره نشده است.</div>:<div className="memory-list">{memories.map(m=><div className="memory-row" key={m.id}><div><span className="memory-category">{m.category} · اهمیت {m.importance}/5</span><p>{m.content}</p></div><button className="icon-button" onClick={()=>deleteMemory(m.id)}><Trash2 size={15}/></button></div>)}</div>}</>}
      {view==="settings"&&<><div className="eyebrow"><Settings size={14}/> PROVIDER SETTINGS</div><h1>اتصال هوش مصنوعی</h1><p className="intro">کلید API فقط در فایل محلی backend/.env قرار می‌گیرد و به مرورگر ارسال نمی‌شود.</p><div className="feature-card settings-card"><h3>وضعیت اتصال</h3><p>{provider?.configured?"کلید و مدل تنظیم شده‌اند.":"هنوز API Key و مدل تنظیم نشده‌اند."}</p><p>مدل: {provider?.model||"تنظیم نشده"}</p><p>برای فعال‌سازی، AI_API_KEY و AI_MODEL را در backend/.env وارد کن و سرور را دوباره اجرا کن.</p></div></>}
      {view==="home"&&<><div className="eyebrow"><Sparkles size={14}/> فضای خصوصی تو</div><h1>دنیای خودت را<br/><em>شخصی‌سازی کن.</em></h1><p className="intro">شخصیت بساز، با او گفت‌وگو کن و خاطرات مکالماتت را در کامپیوتر خودت نگه دار.</p><div className="hero-card"><div className="orb"><Heart size={32} fill="currentColor"/></div><div className="hero-copy"><span className="card-kicker">شروع تجربه تو</span><h2>یک همراه جدید خلق کن.</h2><p>نام، اخلاقیات، علایق و داستان شخصیت را خودت تعیین کن.</p></div><button className="create-button" onClick={()=>setView("create")}><Plus size={17}/> ساخت شخصیت</button></div><div className="section-head"><div><span className="card-kicker">شخصیت‌های تو</span><h2>همراه‌های من</h2></div><span className="muted">{companions.length} شخصیت</span></div>{companions.length===0?<div className="empty-state"><Heart size={25}/><p>هنوز شخصیتی نساختی. اولین همراهت را خلق کن.</p></div>:<div className="companion-grid">{companions.map(c=><article className="companion-card" key={c.id}><div className="companion-top"><div className="avatar">{c.avatar_url?<img src={c.avatar_url} alt={c.name}/>:c.name.slice(0,1)}</div><div className="companion-actions"><button className="icon-button" title="ویرایش شخصیت" onClick={()=>editCompanion(c)}><Pencil size={15}/></button><button className="icon-button" title="حذف شخصیت" onClick={()=>remove(c)}><Trash2 size={15}/></button></div></div><h3>{c.name} <small>{c.age} سال</small></h3><p>{c.short_description||c.traits.join("، ")}</p><div className="card-actions"><button className="primary full" onClick={()=>openChat(c)} disabled={busy}><MessageCircle size={15}/> شروع گفت‌وگو</button><button className="secondary full" onClick={()=>loadMemories(c)}>حافظه</button><button className="secondary full" onClick={()=>loadTimeline(c)}>خط زمانی</button></div></article>)}</div>}{selected&&<div className="history-panel"><div className="section-head"><div><span className="card-kicker">HISTORY</span><h2>مکالمات {selected.name}</h2></div><button className="secondary" onClick={()=>loadSessions(selected)}>به‌روزرسانی</button></div>{sessions.length===0?<p className="muted">هنوز مکالمه‌ای ثبت نشده است.</p>:sessions.map(s=><button className="history-item" key={s.id} onClick={()=>resumeChat(selected,s)}>{s.title} <span>{s.created_at?new Date(s.created_at).toLocaleString("fa-IR"):""}</span></button>)}</div>}<div className="feature-grid"><article className="feature-card"><div className="feature-icon pink"><Heart size={18}/></div><h3>شخصیت‌سازی</h3><p>اخلاقیات، لحن، علایق و دستورالعمل اختصاصی.</p><span>فعال</span></article><article className="feature-card"><div className="feature-icon violet"><Brain size={18}/></div><h3>حافظه هوشمند</h3><p>حافظه اختصاصی، پیشنهاد خاطره و بازیابی مرتبط با پیام.</p><span>فعال</span></article><article className="feature-card"><div className="feature-icon blue"><MessageCircle size={18}/></div><h3>گفت‌وگوهای خصوصی</h3><p>تاریخچه پیام‌ها در دیتابیس محلی ذخیره می‌شود.</p><span>فعال با API</span></article></div></>}
      {error&&<div className="error-banner">{error}</div>}
      <footer className="status-footer"><span className={health?"status-dot":"status-dot offline"}/>{health?"Backend متصل است · دیتابیس محلی آماده":"Backend در دسترس نیست · سرویس محلی را اجرا کن"}<span className="footer-right">اطلاعات روی دستگاه تو</span></footer>
    </div></section>
  </main>;
}
