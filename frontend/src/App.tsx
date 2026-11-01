import { FormEvent, useEffect, useRef, useState } from "react";
import { Heart, Brain, MessageCircle, Plus, ShieldCheck, Sparkles, Send, ArrowLeft, Settings, Trash2, Pencil, Clock3, CalendarHeart, Archive, Download, Upload, ImagePlus, HardDrive, RefreshCw } from "lucide-react";


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

type PersonalityConfig = { preset:"custom"|"gentle"|"playful"|"romantic"|"serious"; humor:number; warmth:number; seriousness:number; expressiveness:number; voice_style:string; backstory:string; voice_model:string };
type Companion = { id:string; name:string; age:number; short_description:string; personality_prompt:string; traits:string[]; interests:string[]; personality_config:PersonalityConfig; avatar_url?:string|null };
type Session = { id:string; companion_id:string; title:string; created_at?:string };
type Message = { id:string; role:string; content:string };
type Memory = { id:string; category:string; content:string; importance:number; layer?:"semantic"|"episodic"|"preference"; confidence?:number; source_session_id?:string|null; access_count?:number; last_accessed_at?:string|null; updated_at?:string };
type Candidate = { category:string; content:string; importance:number };
type MemoryMatch = { memory_id:string; category:string; content:string; kind:"duplicate"|"potential_conflict"|"related"; similarity:number; reason:string };
type MemoryCheckResult = { safe_to_save:boolean; matches:MemoryMatch[] };
type MemoryReview = { item:Candidate; matches:MemoryMatch[]; sourceSessionId:string|null; origin:"candidate"|"manual" };
type EmotionalState = { mood:string; closeness:number; trust:number; energy:number; interaction_count:number };
type TimelineEvent = { id:string; title:string; description:string; event_type:string; occurred_at:string };
type ConversationSummary = { id:string; session_id:string; summary:string; message_count:number; updated_at:string };
type CompanionPreference = { id:string; companion_id:string; category:string; content:string; source_session_id:string|null; confirmed_at:string; created_at:string };
type InsightSuggestions = { preferences:{category:string;content:string}[]; events:{title:string;description:string;event_type:string}[] };
type SystemStatus = { database:string; database_bytes:number; media_files:number; avatar_files:number; safety_backups:number; last_safety_backup:string|null; backup_format_version:number; local_only:boolean };
type SystemAsset = { companion_id:string; companion_name:string; avatar_url:string; storage:"local"|"external"; exists:boolean; size_bytes:number|null };

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
  const [view,setView]=useState<"home"|"create"|"chat"|"settings"|"memory"|"edit"|"timeline"|"preferences"|"system">("home");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [health,setHealth]=useState(false);
  const [provider,setProvider]=useState<{configured:boolean;model:string}|null>(null);
  const [memories,setMemories]=useState<Memory[]>([]);
  const [candidates,setCandidates]=useState<Candidate[]>([]);
  const [memoryReview,setMemoryReview]=useState<MemoryReview|null>(null);
  const [memoryReviewBusy,setMemoryReviewBusy]=useState(false);
  const [emotionalState,setEmotionalState]=useState<EmotionalState|null>(null);
  const [timelineEvents,setTimelineEvents]=useState<TimelineEvent[]>([]);
  const [conversationSummaries,setConversationSummaries]=useState<ConversationSummary[]>([]);
  const [approvedPreferences,setApprovedPreferences]=useState<CompanionPreference[]>([]);
  const [insightSuggestions,setInsightSuggestions]=useState<InsightSuggestions>({preferences:[],events:[]});
  const [insightBusy,setInsightBusy]=useState(false);
  const [preferenceDraft,setPreferenceDraft]=useState({category:"communication_style",content:""});
  const [systemStatus,setSystemStatus]=useState<SystemStatus|null>(null);
  const [systemAssets,setSystemAssets]=useState<SystemAsset[]>([]);
  const [backupBusy,setBackupBusy]=useState(false);
  const [restoreBusy,setRestoreBusy]=useState(false);
  const [restoreFile,setRestoreFile]=useState<File|null>(null);
  const [avatarFile,setAvatarFile]=useState<File|null>(null);
  const [avatarPreview,setAvatarPreview]=useState("");
  const [summaryBusy,setSummaryBusy]=useState(false);
  const [editingMemoryId,setEditingMemoryId]=useState<string|null>(null);
  const [memoryDraft,setMemoryDraft]=useState({category:"personal_context",content:"",importance:3});
  const [eventForm,setEventForm]=useState({title:"",description:"",event_type:"memory"});
  const [form,setForm]=useState({name:"",age:24,short_description:"",personality_prompt:"",traits:"مهربان، شوخ‌طبع",interests:"موسیقی، فیلم، سفر",avatar_url:""});
  const [editingId,setEditingId]=useState<string|null>(null);
  const defaultPersonality:PersonalityConfig={preset:"custom",humor:55,warmth:70,seriousness:35,expressiveness:65,voice_style:"صمیمی و طبیعی",backstory:"",voice_model:""};
  const [personality,setPersonality]=useState<PersonalityConfig>(defaultPersonality);
  const [speechRate,setSpeechRate]=useState(1);
  const [speechPitch,setSpeechPitch]=useState(1);
  const [speaking,setSpeaking]=useState(false);
  const [listening,setListening]=useState(false);
  const [localRecording,setLocalRecording]=useState(false);
  const mediaRecorderRef=useRef<MediaRecorder|null>(null);
  const audioChunksRef=useRef<Blob[]>([]);
  const [autoSpeak,setAutoSpeak]=useState(false);
  const [localVoiceConfigured,setLocalVoiceConfigured]=useState(false);
  const [ttsVoices,setTtsVoices]=useState<{id:string;name:string}[]>([]);
  const [localTtsConfigured,setLocalTtsConfigured]=useState(false);
  const audioRef=useRef<HTMLAudioElement|null>(null);
  const audioUrlRef=useRef<string|null>(null);
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
  const avatarField=<div className="wide avatar-upload-field"><label>نشانی تصویر شخصیت<input type="url" maxLength={1000} value={form.avatar_url} onChange={e=>{setForm({...form,avatar_url:e.target.value});setAvatarFile(null);}} placeholder="https://example.com/avatar.jpg"/></label><label>یا تصویر را از کامپیوتر انتخاب کن<input type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={e=>{const file=e.target.files?.[0]||null;setAvatarFile(file);if(file)setForm(current=>({...current,avatar_url:""}));}}/></label>{(avatarPreview||form.avatar_url)&&<div className="avatar-preview"><img src={avatarPreview||form.avatar_url} alt="پیش‌نمایش تصویر شخصیت"/><span>{avatarFile?avatarFile.name:"پیش‌نمایش تصویر شخصیت"}</span></div>}<small>تصویر محلی با فرمت JPG، PNG، WEBP یا GIF و حداکثر ۱۰ مگابایت ذخیره می‌شود.</small></div>;
  const personalityStudio=<div className="personality-studio wide"><div className="studio-heading"><Sparkles size={16}/> Personality Studio</div><label>قالب اولیه شخصیت<select value={personality.preset} onChange={e=>applyPreset(e.target.value as PersonalityConfig["preset"])}><option value="custom">شخصی‌سازی‌شده</option><option value="gentle">آرام و مهربان</option><option value="playful">شوخ و پرانرژی</option><option value="romantic">رمانتیک</option><option value="serious">جدی و متین</option></select></label><div className="personality-sliders">{([{key:"humor",label:"شوخ‌طبعی"},{key:"warmth",label:"صمیمیت"},{key:"seriousness",label:"جدیت"},{key:"expressiveness",label:"ابراز احساسات"}] as const).map(item=><label className="personality-range" key={item.key}><span>{item.label}<b>{personality[item.key]}%</b></span><input type="range" min="0" max="100" value={personality[item.key]} onChange={e=>setPersonality({...personality,[item.key]:Number(e.target.value),preset:"custom"})}/></label>)}</div><label>صدای اختصاصی محلی<select value={personality.voice_model||""} onChange={e=>setPersonality({...personality,voice_model:e.target.value})}><option value="">بدون صدای محلی</option>{ttsVoices.map(voice=><option key={voice.id} value={voice.id}>{voice.name}</option>)}</select><small>{localTtsConfigured?"مدل‌های صدای محلی شناسایی شدند":"برای فعال‌سازی، Piper و مدل صدای سازگار را نصب کن."}</small></label><label>سبک صحبت<input maxLength={120} value={personality.voice_style} onChange={e=>setPersonality({...personality,voice_style:e.target.value,preset:"custom"})} placeholder="مثلاً صمیمی، کوتاه و شوخ"/></label><label>گذشته و پیش‌زمینه داستانی<textarea rows={3} maxLength={4000} value={personality.backstory} onChange={e=>setPersonality({...personality,backstory:e.target.value})} placeholder="گذشته و جزئیات داستانی شخصیت را اینجا تعریف کن…"/></label></div>;
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
  const speakLocal=async(text:string)=>{
    if(!selected){setError("ابتدا یک شخصیت انتخاب کن.");return;}
    try{
      stopSpeaking();
      const response=await fetch("/api/voice/tts/synthesize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({companion_id:selected.id,text})});
      if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"تولید صدای محلی ناموفق بود.");}
      const blob=await response.blob();
      if(audioUrlRef.current)URL.revokeObjectURL(audioUrlRef.current);
      const url=URL.createObjectURL(blob);audioUrlRef.current=url;
      const audio=new Audio(url);audioRef.current=audio;
      audio.onended=()=>{URL.revokeObjectURL(url);if(audioUrlRef.current===url)audioUrlRef.current=null;setSpeaking(false);};
      audio.onerror=()=>{setSpeaking(false);setError("پخش فایل صوتی ناموفق بود.");};
      setSpeaking(true);await audio.play();
    }catch(error){setSpeaking(false);setError((error as Error).message);}
  };
  const stopSpeaking=()=>{if("speechSynthesis" in window)window.speechSynthesis.cancel();audioRef.current?.pause();audioRef.current=null;if(audioUrlRef.current){URL.revokeObjectURL(audioUrlRef.current);audioUrlRef.current=null;}setSpeaking(false);};
  const startLocalRecording=async()=>{
    if(localRecording){
      mediaRecorderRef.current?.stop();
      setLocalRecording(false);
      return;
    }
    if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==="undefined"){
      setError("ضبط صدا در این مرورگر پشتیبانی نمی‌شود.");
      return;
    }
    try{
      stopSpeaking();
      setError("");
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      const preferredType=MediaRecorder.isTypeSupported("audio/webm;codecs=opus")?"audio/webm;codecs=opus":"audio/webm";
      const recorder=new MediaRecorder(stream,{mimeType:preferredType});
      audioChunksRef.current=[];
      recorder.ondataavailable=(event)=>{if(event.data.size>0)audioChunksRef.current.push(event.data);};
      recorder.onerror=()=>{setError("ضبط صدا با خطا مواجه شد.");setLocalRecording(false);stream.getTracks().forEach(track=>track.stop());};
      recorder.onstop=async()=>{
        setLocalRecording(false);
        stream.getTracks().forEach(track=>track.stop());
        const audioBlob=new Blob(audioChunksRef.current,{type:recorder.mimeType||"audio/webm"});
        if(!audioBlob.size){setError("صدایی ضبط نشد.");return;}
        setBusy(true);
        try{
          const response=await fetch("/api/voice/transcribe?language=fa",{method:"POST",headers:{"Content-Type":audioBlob.type.split(";")[0]},body:audioBlob});
          const result=await response.json();
          if(!response.ok)throw new Error(result.detail||"تبدیل صدای محلی ناموفق بود.");
          const transcript=String(result.text||"").trim();
          if(transcript)setDraft(current=>current?current+" "+transcript:transcript);
          else setError("متنی از صدای ضبط‌شده تشخیص داده نشد.");
        }catch(error){setError((error as Error).message);}
        finally{setBusy(false);}
      };
      mediaRecorderRef.current=recorder;
      recorder.start();
      setLocalRecording(true);
    }catch(error){
      setError((error as Error).name==="NotAllowedError"?"اجازه استفاده از میکروفون داده نشد.":(error as Error).message);
    }
  };
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

  const load=async()=>{try{const [list,h,p]=await Promise.all([api<Companion[]>("/api/companions"),api<{status:string}>("/api/health"),api<{configured:boolean;model:string}>("/api/settings/provider")]);setCompanions(list);setSelected(current=>current??list[0]??null);if(list.length){api<Session[]>(`/api/companions/${list[0].id}/sessions`).then(setSessions).catch(()=>setSessions([]));}setHealth(h.status==="ok");setProvider(p);api<SystemStatus>("/api/system/status").then(setSystemStatus).catch(()=>setSystemStatus(null));api<{items:SystemAsset[] }>("/api/system/assets").then(result=>setSystemAssets(result.items)).catch(()=>setSystemAssets([]));}catch{setHealth(false);}};
  useEffect(()=>{load();},[]);
  useEffect(()=>{if(!avatarFile){setAvatarPreview("");return;}const url=URL.createObjectURL(avatarFile);setAvatarPreview(url);return ()=>URL.revokeObjectURL(url);},[avatarFile]);
  useEffect(()=>{api<{configured:boolean}>("/api/voice/status").then(status=>setLocalVoiceConfigured(status.configured)).catch(()=>setLocalVoiceConfigured(false));},[]);
  useEffect(()=>{api<{configured:boolean;voices:{id:string;name:string}[]}>("/api/voice/tts/voices").then(result=>{setTtsVoices(result.voices);setLocalTtsConfigured(result.configured);}).catch(()=>{setTtsVoices([]);setLocalTtsConfigured(false);});},[]);
  const refreshSystem=async()=>{
    try{
      const [status,assets]=await Promise.all([
        api<SystemStatus>("/api/system/status"),
        api<{items:SystemAsset[]}>("/api/system/assets")
      ]);
      setSystemStatus(status);setSystemAssets(assets.items);
    }catch(e){setError((e as Error).message);}
  };
  const downloadBackup=async()=>{
    setBackupBusy(true);setError("");
    try{
      const response=await fetch("/api/system/backup");
      if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"ساخت فایل پشتیبان ناموفق بود.");}
      const blob=await response.blob();
      const url=URL.createObjectURL(blob);
      const anchor=document.createElement("a");
      anchor.href=url;anchor.download=`nazi-ai-backup-${new Date().toISOString().replace(/[:.]/g,"-")}.zip`;
      document.body.appendChild(anchor);anchor.click();anchor.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),1500);
      await refreshSystem();
    }catch(e){setError((e as Error).message);}
    finally{setBackupBusy(false);}
  };

  const downloadSafetyBackup=async()=>{
    const filename=systemStatus?.last_safety_backup;
    if(!filename)return;
    try{
      const response=await fetch(`/api/system/safety-backups/${encodeURIComponent(filename)}`);
      if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"دریافت پشتیبان ایمنی ناموفق بود.");}
      const blob=await response.blob();
      const url=URL.createObjectURL(blob);
      const anchor=document.createElement("a");
      anchor.href=url;anchor.download=filename;
      document.body.appendChild(anchor);anchor.click();anchor.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),1500);
    }catch(e){setError((e as Error).message);}
  };
  const restoreBackup=async()=>{
    if(!restoreFile)return;
    const confirmed=window.confirm("بازیابی، اطلاعات فعلی شخصیت‌ها و گفتگوها را با اطلاعات فایل پشتیبان جایگزین می‌کند. قبل از آن یک پشتیبان ایمنی خودکار ساخته می‌شود. ادامه می‌دهی؟");
    if(!confirmed)return;
    setRestoreBusy(true);setError("");
    try{
      const response=await fetch("/api/system/restore",{method:"POST",headers:{"Content-Type":"application/zip"},body:restoreFile});
      const result=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(result.detail||"بازیابی فایل ناموفق بود.");
      window.alert(`بازیابی موفق بود. ${result.companions} شخصیت و ${result.media_files} فایل رسانه‌ای بازیابی شد. برنامه دوباره بارگذاری می‌شود.`);
      window.location.reload();
    }catch(e){setError((e as Error).message);}
    finally{setRestoreBusy(false);}
  };
  const uploadAvatarFile=async(companionId:string,file:File):Promise<Companion>=>{
    const response=await fetch(`/api/companions/${companionId}/avatar`,{method:"POST",headers:{"Content-Type":file.type},body:file});
    if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"بارگذاری تصویر ناموفق بود.");}
    return response.json();
  };
  const removeAssetAvatar=async(companionId:string)=>{
    if(!window.confirm("تصویر این شخصیت حذف شود؟"))return;
    try{
      await api(`/api/companions/${companionId}/avatar`,{method:"DELETE"});
      setCompanions(items=>items.map(item=>item.id===companionId?{...item,avatar_url:null}:item));
      setSystemAssets(items=>items.filter(item=>item.companion_id!==companionId));
      await refreshSystem();
    }catch(e){setError((e as Error).message);}
  };
  const editCompanion=(c:Companion)=>{setAvatarFile(null);setEditingId(c.id);setForm({name:c.name,age:c.age,short_description:c.short_description,personality_prompt:c.personality_prompt,traits:c.traits.join("، "),interests:c.interests.join("، "),avatar_url:c.avatar_url||""});setPersonality(c.personality_config||defaultPersonality);setView("edit");setError("");};
  const updateCompanion=async(e:FormEvent)=>{e.preventDefault();if(!editingId)return;setBusy(true);setError("");try{let updated=await api<Companion>(`/api/companions/${editingId}`,{method:"PATCH",body:JSON.stringify({...form,avatar_url:avatarFile?null:form.avatar_url,personality_config:personality,traits:form.traits.split(/[،,]/).map(x=>x.trim()).filter(Boolean),interests:form.interests.split(/[،,]/).map(x=>x.trim()).filter(Boolean)})});if(avatarFile){try{updated=await uploadAvatarFile(editingId,avatarFile);}catch(uploadError){setError((uploadError as Error).message);}}setCompanions(v=>v.map(c=>c.id===updated.id?updated:c));setSelected(updated);setView("home");setEditingId(null);setAvatarFile(null);await refreshSystem();}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const createCompanion=async(e:FormEvent)=>{e.preventDefault();setBusy(true);setError("");try{let c=await api<Companion>("/api/companions",{method:"POST",body:JSON.stringify({...form,avatar_url:avatarFile?null:form.avatar_url,personality_config:personality,traits:form.traits.split(/[،,]/).map(x=>x.trim()).filter(Boolean),interests:form.interests.split(/[،,]/).map(x=>x.trim()).filter(Boolean)})});if(avatarFile){try{c=await uploadAvatarFile(c.id,avatarFile);}catch(uploadError){setError((uploadError as Error).message);}}setCompanions(v=>[c,...v]);setSelected(c);setView("home");setForm({name:"",age:24,short_description:"",personality_prompt:"",traits:"مهربان، شوخ‌طبع",interests:"موسیقی، فیلم، سفر",avatar_url:""});setAvatarFile(null);setPersonality(defaultPersonality);await refreshSystem();}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const openChat=async(c:Companion)=>{setBusy(true);setError("");try{const s=await api<Session>(`/api/companions/${c.id}/sessions`,{method:"POST"});setSelected(c);setSession(s);setMessages([]);await loadConversationSummaries(c);await loadPreferences(c);const state=await api<EmotionalState>(`/api/companions/${c.id}/emotional-state`);setEmotionalState(state);await loadSessions(c);setView("chat");}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const loadSessions=async(c:Companion)=>{try{setSessions(await api<Session[]>(`/api/companions/${c.id}/sessions`));}catch(e){setError((e as Error).message);}};
  const resumeChat=async(c:Companion,s:Session)=>{setBusy(true);setError("");try{const history=await api<Message[]>(`/api/sessions/${s.id}/messages`);setSelected(c);setSession(s);setMessages(history);await loadConversationSummaries(c);await loadPreferences(c);setView("chat");}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const loadConversationSummaries=async(c:Companion)=>{
    try{setConversationSummaries(await api<ConversationSummary[]>(`/api/companions/${c.id}/summaries`));}
    catch(e){setError((e as Error).message);}
  };
  const saveConversationSummary=async()=>{
    if(!session)return;
    setSummaryBusy(true);setError("");
    try{
      const saved=await api<ConversationSummary>(`/api/sessions/${session.id}/summary`,{method:"POST"});
      setConversationSummaries(current=>[saved,...current.filter(item=>item.session_id!==saved.session_id)]);
      setError("");
    }catch(e){setError((e as Error).message);}
    finally{setSummaryBusy(false);}
  };
  const loadTimeline=async(c:Companion)=>{setSelected(c);setError("");try{setTimelineEvents(await api<TimelineEvent[]>(`/api/companions/${c.id}/timeline`));setView("timeline");}catch(e){setError((e as Error).message);}};
  const addTimelineEvent=async(e:FormEvent)=>{e.preventDefault();if(!selected)return;setBusy(true);setError("");try{const saved=await api<TimelineEvent>(`/api/companions/${selected.id}/timeline`,{method:"POST",body:JSON.stringify(eventForm)});setTimelineEvents(v=>[saved,...v]);setEventForm({title:"",description:"",event_type:"memory"});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const deleteTimelineEvent=async(id:string)=>{if(!selected)return;try{await api(`/api/companions/${selected.id}/timeline/${id}`,{method:"DELETE"});setTimelineEvents(v=>v.filter(item=>item.id!==id));}catch(e){setError((e as Error).message);}};
  const loadPreferences=async(c:Companion)=>{
    try{setApprovedPreferences(await api<CompanionPreference[]>(`/api/companions/${c.id}/preferences`));}
    catch(e){setError((e as Error).message);}
  };
  const openPreferences=async(c:Companion)=>{
    setSelected(c);setError("");
    try{setApprovedPreferences(await api<CompanionPreference[]>(`/api/companions/${c.id}/preferences`));setView("preferences");}
    catch(e){setError((e as Error).message);}
  };
  const deletePreference=async(id:string)=>{
    if(!selected)return;
    try{await api(`/api/companions/${selected.id}/preferences/${id}`,{method:"DELETE"});setApprovedPreferences(items=>items.filter(item=>item.id!==id));}
    catch(e){setError((e as Error).message);}
  };
  const savePreference=async(item:{category:string;content:string})=>{
    if(!selected)return;
    try{
      const saved=await api<CompanionPreference>(`/api/companions/${selected.id}/preferences`,{method:"POST",body:JSON.stringify({...item,source_session_id:session?.companion_id===selected.id?session.id:null})});
      setApprovedPreferences(items=>[saved,...items.filter(existing=>existing.content!==saved.content)]);
      setInsightSuggestions(current=>({...current,preferences:current.preferences.filter(candidate=>candidate!==item)}));
    }catch(e){setError((e as Error).message);}
  };
  const saveSuggestedEvent=async(item:InsightSuggestions["events"][number])=>{
    if(!selected)return;
    try{
      const saved=await api<TimelineEvent>(`/api/companions/${selected.id}/timeline`,{method:"POST",body:JSON.stringify(item)});
      setTimelineEvents(items=>[saved,...items]);
      setInsightSuggestions(current=>({...current,events:current.events.filter(candidate=>candidate!==item)}));
    }catch(e){setError((e as Error).message);}
  };
  const suggestCompanionInsights=async()=>{
    if(!session)return;
    setInsightBusy(true);setError("");
    try{setInsightSuggestions(await api<InsightSuggestions>(`/api/sessions/${session.id}/insight-suggestions`,{method:"POST"}));}
    catch(e){setError((e as Error).message);}
    finally{setInsightBusy(false);}
  };
  const loadMemories=async(c:Companion)=>{setSelected(c);setError("");try{setMemories(await api<Memory[]>(`/api/companions/${c.id}/memories`));await loadConversationSummaries(c);setView("memory");}catch(e){setError((e as Error).message);}};
  const persistMemory=async(item:Candidate,sourceSessionId:string|null,origin:"candidate"|"manual",allowConflicts:boolean)=>{
    if(!selected)return;
    const saved=await api<Memory>(`/api/companions/${selected.id}/memories`,{method:"POST",body:JSON.stringify({...item,source_session_id:sourceSessionId,allow_conflicts:allowConflicts})});
    setMemories(current=>[saved,...current.filter(memory=>memory.id!==saved.id)]);
    if(origin==="candidate")setCandidates(current=>current.filter(candidate=>candidate!==item));
    if(origin==="manual")setMemoryDraft({category:"personal_context",content:"",importance:3});
    setMemoryReview(null);
  };
  const requestMemorySave=async(item:Candidate,sourceSessionId:string|null,origin:"candidate"|"manual")=>{
    if(!selected)return;
    setMemoryReviewBusy(true);setError("");
    try{
      const check=await api<MemoryCheckResult>(`/api/companions/${selected.id}/memories/check`,{method:"POST",body:JSON.stringify({...item,source_session_id:sourceSessionId})});
      if(check.matches.length){
        setMemoryReview({item,matches:check.matches,sourceSessionId,origin});
        return;
      }
      await persistMemory(item,sourceSessionId,origin,false);
    }catch(e){setError((e as Error).message);}
    finally{setMemoryReviewBusy(false);}
  };
  const saveMemory=async(item:Candidate)=>{
    const sourceSessionId=session?.companion_id===selected?.id?session.id:null;
    await requestMemorySave(item,sourceSessionId,"candidate");
  };
  const confirmMemoryAsNew=async()=>{
    if(!memoryReview)return;
    setMemoryReviewBusy(true);
    try{await persistMemory(memoryReview.item,memoryReview.sourceSessionId,memoryReview.origin,true);}
    catch(e){setError((e as Error).message);}
    finally{setMemoryReviewBusy(false);}
  };
  const replaceReviewedMemory=async(match:MemoryMatch)=>{
    if(!selected||!memoryReview)return;
    setMemoryReviewBusy(true);
    try{
      const updated=await api<Memory>(`/api/companions/${selected.id}/memories/${match.memory_id}`,{method:"PATCH",body:JSON.stringify(memoryReview.item)});
      setMemories(current=>current.some(item=>item.id===updated.id)?current.map(item=>item.id===updated.id?updated:item):[updated,...current]);
      if(memoryReview.origin==="candidate")setCandidates(current=>current.filter(item=>item!==memoryReview.item));
      if(memoryReview.origin==="manual")setMemoryDraft({category:"personal_context",content:"",importance:3});
      setMemoryReview(null);
    }catch(e){setError((e as Error).message);}
    finally{setMemoryReviewBusy(false);}
  };
  const suggestMemories=async()=>{if(!session)return;setBusy(true);setError("");try{setCandidates(await api<Candidate[]>(`/api/sessions/${session.id}/memory-suggestions`,{method:"POST"}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const createManualMemory=async(e:FormEvent)=>{
    e.preventDefault();if(!selected||!memoryDraft.content.trim())return;
    await requestMemorySave({...memoryDraft},null,"manual");
  };
  const memoryLayerLabel=(layer?:string)=>layer==="episodic"?"خاطرات رویدادی":layer==="preference"?"ترجیحات تأییدشده":"دانش ماندگار";
  const beginEditMemory=(memory:Memory)=>{setEditingMemoryId(memory.id);setMemoryDraft({category:memory.category,content:memory.content,importance:memory.importance});};
  const saveEditedMemory=async(id:string)=>{
    if(!selected)return;
    try{
      const updated=await api<Memory>(`/api/companions/${selected.id}/memories/${id}`,{method:"PATCH",body:JSON.stringify(memoryDraft)});
      setMemories(items=>items.map(item=>item.id===id?updated:item));
      setEditingMemoryId(null);
    }catch(e){setError((e as Error).message);}
  };
  const deleteMemory=async(id:string)=>{if(!selected)return;try{await api(`/api/companions/${selected.id}/memories/${id}`,{method:"DELETE"});setMemories(v=>v.filter(x=>x.id!==id));}catch(e){setError((e as Error).message);}};
  const send=async(e:FormEvent)=>{e.preventDefault();if(!draft.trim()||!session)return;const content=draft.trim();setDraft("");setMessages(v=>[...v,{id:crypto.randomUUID(),role:"user",content}]);setBusy(true);setError("");try{const m=await api<Message>(`/api/sessions/${session.id}/messages`,{method:"POST",body:JSON.stringify({content})});setMessages(v=>[...v,m]);if(autoSpeak){if(selected?.personality_config?.voice_model)speakLocal(m.content);else speakText(m.content);}if(selected){api<EmotionalState>(`/api/companions/${selected.id}/emotional-state`).then(setEmotionalState).catch(()=>{});}}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  const remove=async(c:Companion)=>{if(!confirm(`شخصیت «${c.name}» و مکالماتش حذف شود؟`))return;try{await api(`/api/companions/${c.id}`,{method:"DELETE"});setCompanions(v=>v.filter(x=>x.id!==c.id));}catch(e){setError((e as Error).message);}};
  return <main className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Heart size={19} fill="currentColor"/></span><span>NAZI <b>AI</b></span></div><div className="side-label">فضای شخصی</div>
      <button className={view==="home"?"nav-item active":"nav-item"} onClick={()=>setView("home")}><MessageCircle size={17}/> داشبورد</button>
      <button className="nav-item" onClick={()=>setView("create")}><Heart size={17}/> ساخت شخصیت</button>
      <button className="nav-item" onClick={()=>setView("settings")}><Settings size={17}/> تنظیمات API</button>
      <button className={view==="system"?"nav-item active":"nav-item"} onClick={()=>setView("system")}><Archive size={17}/> پشتیبان و فایل‌ها</button>
      <div className="side-bottom"><div className="privacy"><ShieldCheck size={17}/><span><b>فضای خصوصی</b><small>اجرا روی همین دستگاه</small></span></div><div className="version">NAZI AI · LOCAL BUILD 0.2</div></div>
    </aside>
    <section className="main-panel"><header className="topbar"><span>دستیار هوشمند شخصی</span><div className="local-pill"><i/> LOCAL MODE</div></header>
    <div className="content">
      {view==="chat"&&selected&&session?<><button className="back-button" onClick={()=>setView("home")}><ArrowLeft size={16}/> بازگشت</button><div className="chat-heading"><div className="avatar">{selected.avatar_url?<img src={selected.avatar_url} alt={selected.name}/>:selected.name.slice(0,1)}</div><div><h2>{selected.name}</h2><p>{selected.short_description||"همراه هوشمند تو"}</p></div></div>{emotionalState&&<div className="state-strip"><span>حال‌وهوای داستانی: {emotionalState.mood==="warm"?"صمیمی":emotionalState.mood==="concerned"?"نگران":"آرام"}</span><span>آشنایی {emotionalState.closeness}%</span><span>انرژی {emotionalState.energy}%</span></div>}<div className="messages">{messages.length===0&&<div className="empty-chat"><Heart size={24}/><p>گفت‌وگو با {selected.name} را شروع کن.</p></div>}{messages.map(m=><div key={m.id} className={m.role==="user"?"bubble user":"bubble assistant"}>{m.content}{m.role==="assistant"&&<><button className="speak-button" type="button" onClick={()=>speakText(m.content)} title="خواندن پاسخ با صدای مرورگر">▶ صدای مرورگر</button>{selected?.personality_config?.voice_model&&<button className="speak-button local-speak" type="button" onClick={()=>speakLocal(m.content)} title="خواندن پاسخ با صدای اختصاصی محلی">♫ صدای اختصاصی</button>}</>}</div>)}{busy&&<div className="typing">در حال فکر کردن…</div>}</div><div className="chat-tools"><button className="secondary" type="button" onClick={startLocalRecording} disabled={busy} aria-pressed={localRecording}>{localRecording?"■ پایان ضبط محلی":"🎙 ضبط محلی با Whisper"}</button><button className="secondary" type="button" onClick={startListening} disabled={busy||localRecording} aria-pressed={listening}>{listening?"توقف تشخیص مرورگر":"تشخیص گفتار مرورگر"}</button><span className={localVoiceConfigured?"voice-engine-status ready":"voice-engine-status"}>{localVoiceConfigured?"Whisper محلی آماده":"Whisper نصب نشده"}</span><span className={localTtsConfigured?"voice-engine-status ready":"voice-engine-status"}>{localTtsConfigured?"Piper محلی آماده":"Piper نصب نشده"}</span><label className="speech-auto"><input type="checkbox" checked={autoSpeak} onChange={e=>setAutoSpeak(e.target.checked)}/> خواندن خودکار پاسخ‌ها</label><button className="secondary" type="button" onClick={saveConversationSummary} disabled={busy||summaryBusy||messages.length<2}>{summaryBusy?"در حال ساخت خلاصه…":"ذخیره خلاصه گفتگو در حافظه"}</button><button className="secondary" type="button" onClick={suggestMemories} disabled={busy}>پیشنهاد خاطرات از این گفت‌وگو</button><button className="secondary" type="button" onClick={suggestCompanionInsights} disabled={busy||insightBusy}>{insightBusy?"در حال تحلیل…":"شناخت ترجیحات و خاطرات مشترک"}</button><button className="secondary" type="button" onClick={stopSpeaking} disabled={!speaking}>توقف صدا</button><label className="speech-control">سرعت صدا <input type="range" min="0.7" max="1.3" step="0.1" value={speechRate} onChange={e=>setSpeechRate(Number(e.target.value))}/></label><label className="speech-control">زیر و بمی <input type="range" min="0.7" max="1.3" step="0.1" value={speechPitch} onChange={e=>setSpeechPitch(Number(e.target.value))}/></label></div>{(insightSuggestions.preferences.length>0||insightSuggestions.events.length>0)&&<div className="memory-suggestions"><b>پیشنهادهای شناخت شخصیت؛ فقط با تأیید تو ذخیره می‌شوند</b>{insightSuggestions.preferences.map((item,i)=><div className="insight-suggestion" key={i}><span><small>ترجیح · {item.category}</small>{item.content}</span><button className="primary" type="button" onClick={()=>savePreference(item)}>تأیید ترجیح</button></div>)}{insightSuggestions.events.map((item,i)=><div className="insight-suggestion" key={`event-${i}`}><span><small>خاطره مشترک · {item.event_type}</small><b>{item.title}</b>{item.description}</span><button className="primary" type="button" onClick={()=>saveSuggestedEvent(item)}>ثبت خاطره</button></div>)}</div>}{candidates.length>0&&<div className="memory-suggestions"><b>خاطرات پیشنهادی؛ برای ذخیره تأیید کن</b>{candidates.map((item,i)=><div className="memory-row" key={i}><span>{item.content}</span><button className="primary" type="button" onClick={()=>saveMemory(item)}>ذخیره</button></div>)}</div>}<form className="composer" onSubmit={send}><input value={draft} onChange={e=>setDraft(e.target.value)} placeholder="پیامت را بنویس…" disabled={busy}/><button disabled={busy||!draft.trim()}><Send size={17}/></button></form></>:null}
      {view==="edit"&&<><div className="eyebrow"><Pencil size={14}/> CHARACTER EDITOR</div><h1>شخصیت را<br/><em>بازطراحی کن.</em></h1><p className="intro">تغییرات در شخصیت ذخیره می‌شوند و در گفت‌وگوهای بعدی اعمال خواهند شد.</p><form className="creator-form" onSubmit={updateCompanion}><label>نام شخصیت<input required maxLength={80} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>سن (۱۸ سال به بالا)<input type="number" min="18" max="99" value={form.age} onChange={e=>setForm({...form,age:Number(e.target.value)})}/></label><label>توضیح کوتاه<input value={form.short_description} onChange={e=>setForm({...form,short_description:e.target.value})}/></label><label>ویژگی‌های شخصیتی<input value={form.traits} onChange={e=>setForm({...form,traits:e.target.value})}/></label><label>علایق<input value={form.interests} onChange={e=>setForm({...form,interests:e.target.value})}/></label>{avatarField}{personalityStudio}<label className="wide">پرامپت و داستان شخصیت<textarea rows={7} value={form.personality_prompt} onChange={e=>setForm({...form,personality_prompt:e.target.value})}/></label><div className="form-actions"><button className="primary" disabled={busy}><Pencil size={16}/>{busy?"در حال ذخیره…":"ذخیره تغییرات"}</button><button type="button" className="secondary" onClick={()=>setView("home")}>انصراف</button></div></form></>}
      {view==="create"&&<><div className="eyebrow"><Sparkles size={14}/> CHARACTER STUDIO</div><h1>شخصیت دلخواهت را<br/><em>خلق کن.</em></h1><p className="intro">یک شخصیت داستانی بزرگسال با هویت و لحن اختصاصی بساز.</p><form className="creator-form" onSubmit={createCompanion}><label>نام شخصیت<input required maxLength={80} value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="مثلاً نازنین"/></label><label>سن (۱۸ سال به بالا)<input type="number" min="18" max="99" value={form.age} onChange={e=>setForm({...form,age:Number(e.target.value)})}/></label><label>توضیح کوتاه<input value={form.short_description} onChange={e=>setForm({...form,short_description:e.target.value})} placeholder="مثلاً پرانرژی و اهل موسیقی"/></label><label>ویژگی‌های شخصیتی<input value={form.traits} onChange={e=>setForm({...form,traits:e.target.value})}/></label><label>علایق<input value={form.interests} onChange={e=>setForm({...form,interests:e.target.value})}/></label>{avatarField}{personalityStudio}<label className="wide">پرامپت و داستان شخصیت<textarea rows={5} value={form.personality_prompt} onChange={e=>setForm({...form,personality_prompt:e.target.value})} placeholder="درباره اخلاقیات، شیوه صحبت، گذشته داستانی و علایقش توضیح بده…"/></label><div className="form-actions"><button className="primary" disabled={busy}><Plus size={16}/> {busy?"در حال ساخت…":"ساخت شخصیت"}</button><button type="button" className="secondary" onClick={()=>setView("home")}>انصراف</button></div></form></>}
      {view==="timeline"&&selected&&<><div className="eyebrow"><CalendarHeart size={14}/> RELATIONSHIP TIMELINE</div><h1>داستان مشترک<br/><em>{selected.name}</em></h1><p className="intro">اتفاقات مهمی که می‌خواهی این شخصیت در داستان مشترکتان به یاد داشته باشد.</p><form className="timeline-form" onSubmit={addTimelineEvent}><label>عنوان اتفاق<input required maxLength={120} value={eventForm.title} onChange={e=>setEventForm({...eventForm,title:e.target.value})} placeholder="مثلاً اولین گفت‌وگوی طولانی"/></label><label>نوع اتفاق<select value={eventForm.event_type} onChange={e=>setEventForm({...eventForm,event_type:e.target.value})}><option value="memory">خاطره</option><option value="milestone">نقطه عطف</option><option value="first_time">اولین تجربه</option><option value="shared_interest">علاقه مشترک</option><option value="custom">سایر</option></select></label><label className="wide">توضیحات<textarea rows={3} maxLength={2000} value={eventForm.description} onChange={e=>setEventForm({...eventForm,description:e.target.value})} placeholder="جزئیات این اتفاق را بنویس…"/></label><button className="primary" disabled={busy}><Plus size={15}/> ثبت در خط زمانی</button></form>{timelineEvents.length===0?<div className="empty-state">هنوز اتفاقی ثبت نشده است. اولین خاطره را خودت اضافه کن.</div>:<div className="timeline-list">{timelineEvents.map(item=><article className="timeline-event" key={item.id}><div className="timeline-marker"><Clock3 size={15}/></div><div className="timeline-event-body"><span className="memory-category">{item.event_type} · {new Date(item.occurred_at).toLocaleDateString("fa-IR")}</span><h3>{item.title}</h3>{item.description&&<p>{item.description}</p>}</div><button className="icon-button" title="حذف رویداد" onClick={()=>deleteTimelineEvent(item.id)}><Trash2 size={15}/></button></article>)}</div>}</>}
      {view==="preferences"&&selected&&<><div className="eyebrow"><Sparkles size={14}/> CHARACTER EVOLUTION</div><h1>شناخت و ترجیحات<br/><em>{selected.name}</em></h1><p className="intro">این موارد فقط از گفته‌های صریح تو پیشنهاد می‌شوند و پس از تأیید، در گفتگوهای بعدی برای تنظیم لحن و رفتار شخصیت استفاده خواهند شد. هیچ ترجیحی بدون تأیید ذخیره نمی‌شود.</p><div className="summary-vault"><b>ترجیحات تأییدشده ({approvedPreferences.length})</b>{approvedPreferences.length===0?<p>هنوز ترجیحی تأیید نشده است. از داخل گفتگو می‌توانی پیشنهادها را استخراج کنی یا موارد را دستی اضافه کنی.</p>:approvedPreferences.map(item=><article className="preference-card" key={item.id}><div><small>{item.category} · تأییدشده</small><p>{item.content}</p></div><button className="icon-button" title="حذف ترجیح" onClick={()=>deletePreference(item.id)}><Trash2 size={15}/></button></article>)}</div><form className="memory-create-form" onSubmit={async e=>{e.preventDefault();if(!preferenceDraft.content.trim())return;await savePreference(preferenceDraft);setPreferenceDraft({category:"communication_style",content:""});}}><b>افزودن ترجیح دستی</b><label>دسته‌بندی<select value={preferenceDraft.category} onChange={e=>setPreferenceDraft(v=>({...v,category:e.target.value}))}><option value="communication_style">سبک ارتباط</option><option value="interests">علایق</option><option value="boundaries">حد و مرزها</option><option value="format">قالب پاسخ</option><option value="other">سایر</option></select></label><label>ترجیح<textarea required maxLength={1200} value={preferenceDraft.content} onChange={e=>setPreferenceDraft(v=>({...v,content:e.target.value}))} placeholder="مثلاً پاسخ‌ها کوتاه و صمیمی باشند."/></label><button className="primary" type="submit" disabled={!preferenceDraft.content.trim()}>ذخیره ترجیح</button></form><button className="secondary" onClick={()=>setView("home")}>بازگشت به داشبورد</button></>}
      {view==="memory"&&selected&&<><div className="eyebrow"><Brain size={14}/> MEMORY VAULT</div><h1>خاطرات {selected.name}</h1><p className="intro">خاطرات ذخیره‌شده فقط به همین شخصیت تعلق دارند. می‌توانی آن‌ها را حذف کنی. خلاصه گفتگوها نیز برای یادآوری موضوعات جلسات قبلی استفاده می‌شود.</p><form className="memory-create-form" onSubmit={createManualMemory}><b>ثبت خاطره جدید</b><label>دسته‌بندی<select value={memoryDraft.category} onChange={e=>setMemoryDraft(v=>({...v,category:e.target.value}))}><option value="personal_context">اطلاعات شخصی</option><option value="preference">علایق و ترجیحات</option><option value="important_event">اتفاق مهم</option><option value="shared_story">خاطره مشترک</option></select></label><label>متن خاطره<textarea required maxLength={3000} value={memoryDraft.content} onChange={e=>setMemoryDraft(v=>({...v,content:e.target.value}))} placeholder="مثلاً کاربر موسیقی سنتی را دوست دارد."/></label><label>اهمیت: {memoryDraft.importance}/5<input type="range" min="1" max="5" value={memoryDraft.importance} onChange={e=>setMemoryDraft(v=>({...v,importance:Number(e.target.value)}))}/></label><button className="primary" type="submit" disabled={!memoryDraft.content.trim()}>ذخیره خاطره</button></form><div className="summary-vault"><b>خلاصه گفتگوهای قبلی ({conversationSummaries.length})</b>{conversationSummaries.length===0?<p>هنوز خلاصه‌ای ذخیره نشده است.</p>:conversationSummaries.map(item=><article className="summary-card" key={item.id}><span>{item.message_count} پیام · {new Date(item.updated_at).toLocaleDateString("fa-IR")}</span><p>{item.summary}</p></article>)}</div>{memories.length===0?<div className="empty-state">هنوز خاطره‌ای ذخیره نشده است.</div>:<div className="memory-list">{memories.map(m=><div className="memory-row" key={m.id}><div className="memory-row-content">{editingMemoryId===m.id?<div className="memory-edit-form"><label>دسته‌بندی<input value={memoryDraft.category} onChange={e=>setMemoryDraft(v=>({...v,category:e.target.value}))}/></label><label>متن خاطره<textarea value={memoryDraft.content} onChange={e=>setMemoryDraft(v=>({...v,content:e.target.value}))}/></label><label>اهمیت: {memoryDraft.importance}/5<input type="range" min="1" max="5" value={memoryDraft.importance} onChange={e=>setMemoryDraft(v=>({...v,importance:Number(e.target.value)}))}/></label><div className="memory-edit-actions"><button className="primary" onClick={()=>saveEditedMemory(m.id)}>ذخیره تغییرات</button><button className="secondary" onClick={()=>setEditingMemoryId(null)}>انصراف</button></div></div>:<><span className="memory-category">{m.category} · اهمیت {m.importance}/5</span><p>{m.content}</p></>}</div><div className="memory-row-actions">{editingMemoryId!==m.id&&<button className="icon-button" title="ویرایش خاطره" onClick={()=>beginEditMemory(m)}><Pencil size={15}/></button>}<button className="icon-button" title="حذف خاطره" onClick={()=>deleteMemory(m.id)}><Trash2 size={15}/></button></div></div>)}</div>}</>}
      {view==="system"&&<><div className="eyebrow"><Archive size={14}/> LOCAL DATA CENTER</div><h1>پشتیبان و فایل‌ها</h1><p className="intro">مدیریت امن اطلاعات محلی، فایل‌های شخصیت‌ها و انتقال پروژه به کامپیوتر دیگر.</p><div className="system-stats"><article><HardDrive size={18}/><b>{systemStatus?Math.ceil(systemStatus.database_bytes/1024/1024*10)/10:"—"} MB</b><span>حجم دیتابیس</span></article><article><ImagePlus size={18}/><b>{systemStatus?.media_files??"—"}</b><span>فایل‌های رسانه‌ای</span></article><article><ShieldCheck size={18}/><b>{systemStatus?.safety_backups??"—"}</b><span>پشتیبان‌های ایمنی</span></article></div><div className="system-grid"><section className="system-card"><div className="system-card-title"><Download size={18}/><h2>پشتیبان‌گیری کامل</h2></div><p>تمام شخصیت‌ها، پیام‌ها، خاطرات، ترجیحات، خط زمانی و تصاویر محلی در یک فایل ZIP قرار می‌گیرند.</p><ul><li>پشتیبان‌گیری سازگار از SQLite</li><li>بررسی سلامت دیتابیس و چک‌سام فایل‌ها</li><li>بدون ذخیره کلید API در فایل پشتیبان</li></ul><button className="primary" onClick={downloadBackup} disabled={backupBusy}>{backupBusy?<RefreshCw size={16} className="spin"/>:<Download size={16}/>} {backupBusy?"در حال ساخت پشتیبان…":"ساخت و دریافت فایل پشتیبان"}</button>{systemStatus?.last_safety_backup&&<div className="safety-backup-row"><span>آخرین پشتیبان ایمنی: {systemStatus.last_safety_backup}</span><button className="secondary" type="button" onClick={downloadSafetyBackup}><Download size={14}/> دریافت</button></div>}</section><section className="system-card"><div className="system-card-title"><Upload size={18}/><h2>بازیابی پشتیبان</h2></div><p>فایل ZIP ساخته‌شده توسط Nazi AI را انتخاب کن. اطلاعات فعلی جایگزین می‌شوند.</p><label className="restore-picker">انتخاب فایل پشتیبان<input type="file" accept=".zip,application/zip" onChange={e=>setRestoreFile(e.target.files?.[0]||null)}/></label>{restoreFile&&<div className="selected-file"><Archive size={16}/><span>{restoreFile.name}</span><small>{(restoreFile.size/1024/1024).toFixed(1)} MB</small></div>}<button className="danger-button" onClick={restoreBackup} disabled={!restoreFile||restoreBusy}>{restoreBusy?"در حال بازیابی…":"بازیابی و جایگزینی اطلاعات"}</button><small className="system-warning">قبل از بازیابی، یک پشتیبان خودکار از اطلاعات فعلی ساخته می‌شود.</small></section></div><section className="system-card asset-manager"><div className="system-card-title"><ImagePlus size={18}/><h2>مدیریت تصاویر شخصیت‌ها</h2><button className="secondary" onClick={refreshSystem}><RefreshCw size={14}/> به‌روزرسانی</button></div>{systemAssets.length===0?<p className="muted">هنوز تصویری برای شخصیت‌ها ثبت نشده است.</p>:systemAssets.map(asset=><article className="asset-row" key={asset.companion_id}>{asset.storage==="local"&&asset.exists?<img src={asset.avatar_url} alt={asset.companion_name}/>:<div className="asset-placeholder"><ImagePlus size={18}/></div>}<div className="asset-info"><b>{asset.companion_name}</b><small>{asset.storage==="local"?(asset.exists?"ذخیره‌شده روی همین دستگاه":"فایل تصویر پیدا نشد"):"تصویر با نشانی خارجی"}</small>{asset.size_bytes!==null&&<small>{(asset.size_bytes/1024).toFixed(0)} KB</small>}</div><button className="icon-button" title="حذف تصویر" onClick={()=>removeAssetAvatar(asset.companion_id)}><Trash2 size={15}/></button></article>)}</section><section className="transfer-note"><b>نکته مهم برای انتقال به لپ‌تاپ دیگر</b><p>فایل ZIP شامل دیتابیس و تصاویر است؛ کلید API داخل آن قرار نمی‌گیرد. بعد از انتقال، فایل backend/.env را جداگانه روی دستگاه جدید تنظیم کن. مدل‌های Whisper و Piper نیز در صورت نصب، باید جداگانه منتقل شوند.</p></section><button className="secondary" onClick={()=>setView("home")}>بازگشت به داشبورد</button></>}
      {view==="settings"&&<><div className="eyebrow"><Settings size={14}/> PROVIDER SETTINGS</div><h1>اتصال هوش مصنوعی</h1><p className="intro">کلید API فقط در فایل محلی backend/.env قرار می‌گیرد و به مرورگر ارسال نمی‌شود.</p><div className="feature-card settings-card"><h3>وضعیت اتصال</h3><p>{provider?.configured?"کلید و مدل تنظیم شده‌اند.":"هنوز API Key و مدل تنظیم نشده‌اند."}</p><p>مدل: {provider?.model||"تنظیم نشده"}</p><p>برای فعال‌سازی، AI_API_KEY و AI_MODEL را در backend/.env وارد کن و سرور را دوباره اجرا کن.</p></div></>}
      {view==="home"&&<><div className="eyebrow"><Sparkles size={14}/> فضای خصوصی تو</div><h1>دنیای خودت را<br/><em>شخصی‌سازی کن.</em></h1><p className="intro">شخصیت بساز، با او گفت‌وگو کن و خاطرات مکالماتت را در کامپیوتر خودت نگه دار.</p><div className="hero-card"><div className="orb"><Heart size={32} fill="currentColor"/></div><div className="hero-copy"><span className="card-kicker">شروع تجربه تو</span><h2>یک همراه جدید خلق کن.</h2><p>نام، اخلاقیات، علایق و داستان شخصیت را خودت تعیین کن.</p></div><button className="create-button" onClick={()=>setView("create")}><Plus size={17}/> ساخت شخصیت</button></div><div className="section-head"><div><span className="card-kicker">شخصیت‌های تو</span><h2>همراه‌های من</h2></div><span className="muted">{companions.length} شخصیت</span></div>{companions.length===0?<div className="empty-state"><Heart size={25}/><p>هنوز شخصیتی نساختی. اولین همراهت را خلق کن.</p></div>:<div className="companion-grid">{companions.map(c=><article className="companion-card" key={c.id}><div className="companion-top"><div className="avatar">{c.avatar_url?<img src={c.avatar_url} alt={c.name}/>:c.name.slice(0,1)}</div><div className="companion-actions"><button className="icon-button" title="ویرایش شخصیت" onClick={()=>editCompanion(c)}><Pencil size={15}/></button><button className="icon-button" title="حذف شخصیت" onClick={()=>remove(c)}><Trash2 size={15}/></button></div></div><h3>{c.name} <small>{c.age} سال</small></h3><p>{c.short_description||c.traits.join("، ")}</p><div className="card-actions"><button className="primary full" onClick={()=>openChat(c)} disabled={busy}><MessageCircle size={15}/> شروع گفت‌وگو</button><button className="secondary full" onClick={()=>loadMemories(c)}>حافظه</button><button className="secondary full" onClick={()=>loadTimeline(c)}>خط زمانی</button><button className="secondary full" onClick={()=>openPreferences(c)}>ترجیحات شخصیت</button></div></article>)}</div>}{selected&&<div className="history-panel"><div className="section-head"><div><span className="card-kicker">HISTORY</span><h2>مکالمات {selected.name}</h2></div><button className="secondary" onClick={()=>loadSessions(selected)}>به‌روزرسانی</button></div>{sessions.length===0?<p className="muted">هنوز مکالمه‌ای ثبت نشده است.</p>:sessions.map(s=><button className="history-item" key={s.id} onClick={()=>resumeChat(selected,s)}>{s.title} <span>{s.created_at?new Date(s.created_at).toLocaleString("fa-IR"):""}</span></button>)}</div>}<div className="feature-grid"><article className="feature-card"><div className="feature-icon pink"><Heart size={18}/></div><h3>شخصیت‌سازی</h3><p>اخلاقیات، لحن، علایق و دستورالعمل اختصاصی.</p><span>فعال</span></article><article className="feature-card"><div className="feature-icon violet"><Brain size={18}/></div><h3>حافظه هوشمند</h3><p>حافظه اختصاصی، پیشنهاد خاطره و بازیابی مرتبط با پیام.</p><span>فعال</span></article><article className="feature-card"><div className="feature-icon blue"><MessageCircle size={18}/></div><h3>گفت‌وگوهای خصوصی</h3><p>تاریخچه پیام‌ها در دیتابیس محلی ذخیره می‌شود.</p><span>فعال با API</span></article></div></>}
      {error&&<div className="error-banner">{error}</div>}
      <footer className="status-footer"><span className={health?"status-dot":"status-dot offline"}/>{health?"Backend متصل است · دیتابیس محلی آماده":"Backend در دسترس نیست · سرویس محلی را اجرا کن"}<span className="footer-right">اطلاعات روی دستگاه تو</span></footer>
    </div></section>
  </main>;
}
