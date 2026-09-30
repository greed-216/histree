import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type { Topic,Person,Event,PageResult } from '@histree/shared-types';
import { useResource } from '../hooks/useResource';
import { EntryCard,LoadState } from '../components/Reading';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { TopicExplorer } from '../components/TopicExplorer';

function TopicSection({slug,section,index}:{slug:string;section:Topic['sections'][number];index:number}) {
 const ref=useRef<HTMLElement>(null);const [visible,setVisible]=useState(false);
 useEffect(()=>{
  if(!ref.current)return;
  const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){setVisible(true);observer.disconnect();}},{rootMargin:'300px'});
  observer.observe(ref.current);return ()=>observer.disconnect();
 },[]);
 const result=useInfiniteResource<PageResult<Person|Event>>(visible?`/catalog/nodes?${new URLSearchParams({topic:slug,section:String(index)})}`:undefined);
 return <section ref={ref} id={`chapter-${index}`} className="scroll-mt-28">
  <p className="eyebrow">{String(index+1).padStart(2,'0')} / 阅读线索</p><h2 className="font-serif text-2xl mt-2">{section.heading}</h2>
  <p className="leading-8 text-slate-600 whitespace-pre-line mt-4">{section.body}</p><LoadState {...result}/>
  <div className="grid sm:grid-cols-2 gap-4 mt-6">{result.data?.items.map(node=><EntryCard key={node.id} node={node}/>)}</div>
  {result.data&&section.node_ids.length>0&&result.data.items.length===0&&<p className="text-sm text-slate-500">部分关联条目正在修订，发布后即可阅读。</p>}
  {visible&&<InfiniteScroll {...result} count={result.data?.items.length} label="章节条目"/>}
 </section>;
}
export function TopicPage() {
 const {slug}=useParams();const topic=useResource<Topic>(`/topics/${slug}`);
 if(topic.loading||topic.error)return <LoadState {...topic}/>;if(!topic.data)return null;
 const data=topic.data;
 return <div className="space-y-10 pb-12"><Link to="/" className="text-sm text-teal-700">← 专题探索</Link>
  <header className="max-w-3xl"><p className="eyebrow mt-6">专题阅读 / {data.sections.length} 个章节</p><h1 className="font-serif text-4xl md:text-5xl mt-4">{data.title}</h1><p className="text-lg leading-8 text-slate-600 mt-6">{data.description}</p></header>
  <TopicExplorer key={data.id} topicSlug={slug}/>
  <div className="grid lg:grid-cols-[1fr_260px] gap-12"><div className="space-y-12">{data.sections.map((section,index)=><TopicSection key={`${data.id}:${index}`} slug={slug!} section={section} index={index}/>)}</div>
  <aside><nav className="reading-card"><p className="eyebrow mb-4">阅读目录</p>{data.sections.map((s,i)=><a href={`#chapter-${i}`} key={i} className="block py-2 text-sm hover:text-teal-700">{i+1}. {s.heading}</a>)}</nav></aside></div>
 </div>;
}
