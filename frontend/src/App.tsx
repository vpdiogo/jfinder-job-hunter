import { useCallback, useEffect, useRef, useState } from 'react'

import {
  createApplicationProfileFromBase,
  createJobNote,
  createManualJob,
  extractJobDescription,
  extractResume,
  getJobEvaluations,
  getJobNotes,
  getProfessionalBase,
  evaluateSavedJob,
  getProfiles,
  getQueue,
  moveJob,
  updateJobNote,
  updateJobStatus,
  saveProfessionalBase,
  updateProfile,
} from './api'
import type { Evaluation, JobNote, JobQueueItem, JobStatus, Profile } from './types'
import './App.css'

const statuses: JobStatus[] = [
  'discovered',
  'evaluated',
  'interested',
  'applied',
  'recruiter',
  'technical',
  'final',
  'offer',
  'rejected',
]

const nextStatuses: Record<JobStatus, JobStatus[]> = {
  discovered: [],
  evaluated: ['interested'],
  interested: ['applied'],
  applied: ['recruiter', 'rejected'],
  recruiter: ['technical', 'rejected'],
  technical: ['final', 'rejected'],
  final: ['offer', 'rejected'],
  offer: [],
  rejected: [],
}

function toList(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function toLines(value: string): string[] {
  return value.split('\n').map((item) => item.trim()).filter(Boolean)
}

function formatStatus(status: string): string {
  const labels: Record<string, string> = { discovered: "Descoberta", evaluated: "Avaliada", interested: "Interessante", applied: "Candidatura", recruiter: "Recrutador", technical: "Técnica", final: "Final", offer: "Oferta", rejected: "Recusada" }
  return labels[status] ?? status.replaceAll("_", " ")
}

function formatRecommendation(recommendation: string): string {
  return { apply: "Aplicar", review: "Revisar", skip: "Pular" }[recommendation] ?? recommendation
}

function App() {
  const [tab, setTab] = useState<'queue' | 'profile' | 'new-job' | 'base'>('queue')
  const [jobs, setJobs] = useState<JobQueueItem[]>([])
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [professionalBaseState, setProfessionalBaseState] = useState<"loading" | "ready" | "missing" | "error">("loading")
  const [baseResume, setBaseResume] = useState("" )
  const [baseLinks, setBaseLinks] = useState("")
  const [baseSkills, setBaseSkills] = useState("")
  const [baseExperiences, setBaseExperiences] = useState("")
  const [baseEducation, setBaseEducation] = useState("")
  const [baseLanguages, setBaseLanguages] = useState("")
  const [selectedJob, setSelectedJob] = useState<JobQueueItem | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [notes, setNotes] = useState<JobNote[]>([])
  const [noteContent, setNoteContent] = useState("" )
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null)
  const [status, setStatus] = useState<JobStatus | ''>('')
  const [recommendation, setRecommendation] = useState('')
  const [minScore, setMinScore] = useState('')
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null)
  const [profileName, setProfileName] = useState('')
  const [skills, setSkills] = useState('')
  const [targetTitles, setTargetTitles] = useState('')
  const [desiredSeniority, setDesiredSeniority] = useState('')
  const [workModes, setWorkModes] = useState('')
  const [locations, setLocations] = useState('')
  const [timezones, setTimezones] = useState('')
  const [salaryMin, setSalaryMin] = useState('')
  const [salaryMax, setSalaryMax] = useState('')
  const [languages, setLanguages] = useState('')
  const [requiredTechnologies, setRequiredTechnologies] = useState('')
  const [desiredTechnologies, setDesiredTechnologies] = useState('')
  const [manualTitle, setManualTitle] = useState('')
  const [manualCompany, setManualCompany] = useState('')
  const [manualUrl, setManualUrl] = useState('')
  const [manualDescription, setManualDescription] = useState('')
  const [manualProfileId, setManualProfileId] = useState('')
  const [manualResponsibilities, setManualResponsibilities] = useState('')
  const [manualRequiredTechnologies, setManualRequiredTechnologies] = useState('')
  const [manualDesiredTechnologies, setManualDesiredTechnologies] = useState('')
  const [manualSeniority, setManualSeniority] = useState('')
  const [manualWorkMode, setManualWorkMode] = useState('')
  const [manualLanguages, setManualLanguages] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const hasLoadedProfiles = useRef(false)
  const selectedJobRequest = useRef(0)

  const loadQueue = useCallback(async () => {
    try {
      const data = await getQueue({ status: status || undefined, recommendation, minScore })
      setJobs(data)
      setSelectedJob((current) => data.find((job) => job.id === current?.id) ?? null)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Erro ao carregar a fila.')
    } finally {
      setLoading(false)
    }
  }, [status, recommendation, minScore])

  const loadProfiles = useCallback(async () => {
    try {
      const data = await getProfiles()
      setProfiles(data)
      if (!hasLoadedProfiles.current && data.length) {
        selectProfile(data[0])
      }
      hasLoadedProfiles.current = true
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Erro ao carregar perfis.')
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQueue()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQueue])

  useEffect(() => {
    if (!message) return
    const timer = window.setTimeout(() => setMessage(""), 4500)
    return () => window.clearTimeout(timer)
  }, [message])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadProfiles()
      void getProfessionalBase().then((base) => {
        setProfessionalBaseState("ready")
        setBaseResume(base.resume_content)
        setBaseLinks(base.links.join(", "))
        setBaseSkills(base.skills.join(", "))
        setBaseExperiences(base.experiences.join("\n"))
        setBaseEducation(base.education.join("\n"))
        setBaseLanguages(base.languages.join(", "))
      }).catch((error: unknown) => {
        setProfessionalBaseState(error instanceof Error && error.message === "Professional base not found." ? "missing" : "error")
      })
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadProfiles])

  async function selectJob(job: JobQueueItem) {
    const requestId = ++selectedJobRequest.current
    setSelectedJob(job)
    setEvaluations([])
    setNotes([])
    setNoteContent("")
    setEditingNoteId(null)
    try {
      const [jobEvaluations, jobNotes] = await Promise.all([
        getJobEvaluations(job.id),
        getJobNotes(job.id),
      ])
      if (requestId !== selectedJobRequest.current) return
      setEvaluations(jobEvaluations)
      setNotes(jobNotes)
    } catch (error) {
      if (requestId === selectedJobRequest.current) {
        setMessage(error instanceof Error ? error.message : 'Erro ao carregar detalhes.')
      }
    }
  }

  function selectProfile(profile: Profile) {
    setSelectedProfileId(profile.id)
    setProfileName(profile.name)
    setSkills(profile.skills.join(', '))
    setTargetTitles(profile.target_titles.join(', '))
    setDesiredSeniority(profile.desired_seniority ?? '')
    setWorkModes(profile.work_modes.join(', '))
    setLocations(profile.locations.join(', '))
    setTimezones(profile.timezones.join(', '))
    setSalaryMin(profile.salary_min?.toString() ?? '')
    setSalaryMax(profile.salary_max?.toString() ?? '')
    setLanguages(profile.languages.join(', '))
    setRequiredTechnologies(profile.required_technologies.join(', '))
    setDesiredTechnologies(profile.desired_technologies.join(', '))
  }

  async function evaluateJob() {
    if (!selectedJob) return
    if (selectedProfileId === null) {
      setMessage('Selecione ou crie um perfil antes de avaliar a vaga.')
      return
    }
    try {
      const evaluation = await evaluateSavedJob(selectedJob.id, selectedProfileId)
      setMessage('Vaga avaliada.')
      await loadQueue()
      await selectJob({
        ...selectedJob,
        status: 'evaluated',
        score: evaluation.score,
        recommendation: evaluation.recommendation,
      })
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível avaliar a vaga.')
    }
  }

  async function changeStatus(action: 'interest' | 'apply' | JobStatus) {
    if (!selectedJob) return
    try {
      if (action === 'interest' || action === 'apply') {
        await moveJob(selectedJob.id, action)
      } else {
        await updateJobStatus(selectedJob.id, action)
      }
      const nextStatus =
        action === 'interest'
          ? 'interested'
          : action === 'apply'
          ? 'applied'
          : action
      setMessage('Status atualizado.')
      await loadQueue()
      await selectJob({ ...selectedJob, status: nextStatus })
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível atualizar o status.')
    }
  }

  function profileData() {
    return {
      name: profileName.trim() || 'Perfil sem nome',
      skills: toList(skills),
      target_titles: toList(targetTitles),
      desired_seniority: desiredSeniority || null,
      work_modes: toList(workModes),
      locations: toList(locations),
      timezones: toList(timezones),
      salary_min: salaryMin ? Number(salaryMin) : null,
      salary_max: salaryMax ? Number(salaryMax) : null,
      languages: toList(languages),
      required_technologies: toList(requiredTechnologies),
      desired_technologies: toList(desiredTechnologies),
    }
  }

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = profileData()
    if (selectedProfileId === null && professionalBaseState !== "ready") {
      setMessage(
        professionalBaseState === "loading"
          ? "Aguarde o carregamento da base profissional."
          : "Crie uma Base profissional antes de criar um perfil de candidatura.",
      )
      return
    }
    try {
      const profile = selectedProfileId
        ? await updateProfile(selectedProfileId, data)
        : await createApplicationProfileFromBase(data)
      await loadProfiles()
      selectProfile(profile)
      setMessage('Perfil salvo.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível salvar o perfil.')
    }
  }

  async function extractBaseResume() {
    try {
      const extraction = await extractResume(baseResume)
      setBaseSkills(extraction.draft.skills.join(", "))
      setBaseExperiences(extraction.draft.experiences.join("\n"))
      setBaseEducation(extraction.draft.education.join("\n"))
      setBaseLanguages(extraction.draft.languages.join(", "))
      setMessage("Dados extraídos. Revise-os antes de salvar a base profissional.")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível extrair o currículo.")
    }
  }

  async function saveProfessionalBaseForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await saveProfessionalBase({
        resume_content: baseResume, links: toList(baseLinks), skills: toList(baseSkills),
        experiences: toLines(baseExperiences), education: toLines(baseEducation),
        languages: toList(baseLanguages),
      })
      setMessage("Base profissional salva.")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível salvar a base profissional.")
    }
  }

  async function extractManualJob() {
    if (manualDescription.trim().length < 20) {
      setMessage("Cole uma descrição de ao menos 20 caracteres para extrair os dados.")
      return
    }
    try {
      const extraction = await extractJobDescription(manualDescription)
      setManualResponsibilities(extraction.responsibilities.join("\n"))
      setManualRequiredTechnologies(extraction.required_technologies.join(", "))
      setManualDesiredTechnologies(extraction.desired_technologies.join(", "))
      setManualSeniority(extraction.seniority ?? "")
      setManualWorkMode(extraction.work_mode ?? "")
      setManualLanguages(extraction.languages.join(", "))
      setMessage("Dados extraídos. Revise-os antes de salvar.")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível extrair a vaga.")
    }
  }

  async function saveManualJob(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!manualProfileId) {
      setMessage("Selecione o perfil em foco para esta vaga.")
      return
    }
    try {
      const job = await createManualJob({
        profile_id: Number(manualProfileId),
        job: {
          title: manualTitle.trim(), company: manualCompany.trim(), url: manualUrl.trim(),
          description: manualDescription, required_skills: [],
          responsibilities: toLines(manualResponsibilities), source: "manual",
          required_technologies: toList(manualRequiredTechnologies),
          desired_technologies: toList(manualDesiredTechnologies),
          seniority: manualSeniority || null, work_mode: manualWorkMode || null,
          location: null, timezone: null, salary_min: null, salary_max: null,
          languages: toList(manualLanguages),
        },
      })
      await loadQueue()
      setSelectedJob(job)
      setEvaluations(await getJobEvaluations(job.id))
      setTab("queue")
      setMessage("Vaga cadastrada e avaliada com o perfil selecionado.")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível cadastrar a vaga.")
    }
  }

  async function saveJobNote(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedJob || !noteContent.trim()) return
    try {
      if (editingNoteId) {
        await updateJobNote(selectedJob.id, editingNoteId, noteContent.trim())
      } else {
        await createJobNote(selectedJob.id, noteContent.trim())
      }
      setNotes(await getJobNotes(selectedJob.id))
      setNoteContent("")
      setEditingNoteId(null)
      setMessage("Anotação salva.")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível salvar a anotação.")
    }
  }

  const latestEvaluation = evaluations[0]
  const focusProfile = profiles.find((profile) => profile.id === selectedJob?.focus_profile_id)

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">JFinder</p>
          <h1>Seu processo seletivo, em uma só fila.</h1>
        </div>
        <nav aria-label="Navegação principal">
          <button className={tab === 'queue' ? 'active' : ''} onClick={() => setTab('queue')}>Vagas</button>
          <button className={tab === 'profile' ? 'active' : ''} onClick={() => setTab('profile')}>Perfis</button><button className={tab === 'base' ? 'active' : ''} onClick={() => setTab('base')}>Base profissional</button><button className={tab === 'new-job' ? 'active' : ''} onClick={() => setTab('new-job')}>Cadastrar vaga</button>
        </nav>
      </header>

      {message && <div className="toast" role="status">{message}</div>}

      {tab === "base" ? (
        <section className="profile-panel"><div className="section-heading"><div><p className="eyebrow">Base profissional</p><h2>Seu histórico, antes dos recortes para candidaturas</h2></div></div><form onSubmit={(event) => void saveProfessionalBaseForm(event)}><label>Currículo em texto<textarea value={baseResume} onChange={(event) => setBaseResume(event.target.value)} placeholder="Cole aqui o currículo completo" /></label><button type="button" className="secondary" onClick={() => void extractBaseResume()}>Extrair dados do currículo</button><label>Links relevantes, separados por vírgula<input value={baseLinks} onChange={(event) => setBaseLinks(event.target.value)} placeholder="LinkedIn, GitHub, portfólio" /></label><label>Skills, separadas por vírgula<textarea value={baseSkills} onChange={(event) => setBaseSkills(event.target.value)} placeholder="Python, FastAPI, liderança técnica" /></label><label>Experiências, uma por linha<textarea value={baseExperiences} onChange={(event) => setBaseExperiences(event.target.value)} placeholder="Platform Engineer — Acme" /></label><label>Formação, uma por linha<textarea value={baseEducation} onChange={(event) => setBaseEducation(event.target.value)} placeholder="Ciência da Computação" /></label><label>Idiomas, separados por vírgula<input value={baseLanguages} onChange={(event) => setBaseLanguages(event.target.value)} placeholder="English, Portuguese" /></label><button type="submit">Salvar base profissional</button></form></section>
      ) : tab === "new-job" ? (
        <section className="profile-panel">
          <div className="section-heading"><div><p className="eyebrow">Estudar uma vaga</p><h2>Cadastre uma oportunidade para estudar</h2></div></div>
          <form onSubmit={(event) => void saveManualJob(event)}>
            <label>Perfil em foco<select required value={manualProfileId} onChange={(event) => setManualProfileId(event.target.value)}><option value="">Selecione o perfil</option>{profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.name}</option>)}</select></label>
            <label>Cargo<input required value={manualTitle} onChange={(event) => setManualTitle(event.target.value)} placeholder="Tech Lead" /></label>
            <label>Empresa<input required value={manualCompany} onChange={(event) => setManualCompany(event.target.value)} placeholder="Empresa" /></label>
            <label>URL da vaga<input required type="url" value={manualUrl} onChange={(event) => setManualUrl(event.target.value)} placeholder="https://empresa.com/carreiras/vaga" /></label>
            <label>Descrição da vaga<textarea required value={manualDescription} onChange={(event) => setManualDescription(event.target.value)} placeholder="Cole aqui a descrição completa da vaga" /></label>
            <button type="button" className="secondary" onClick={() => void extractManualJob()}>Extrair dados da descrição</button>
            <p className="hint">Revise os dados extraídos antes de salvar.</p>
            <label>Responsabilidades, uma por linha<textarea value={manualResponsibilities} onChange={(event) => setManualResponsibilities(event.target.value)} /></label>
            <label>Tecnologias obrigatórias, separadas por vírgula<input value={manualRequiredTechnologies} onChange={(event) => setManualRequiredTechnologies(event.target.value)} /></label>
            <label>Tecnologias desejáveis, separadas por vírgula<input value={manualDesiredTechnologies} onChange={(event) => setManualDesiredTechnologies(event.target.value)} /></label>
            <label>Senioridade<input value={manualSeniority} onChange={(event) => setManualSeniority(event.target.value)} placeholder="senior" /></label>
            <label>Modalidade<input value={manualWorkMode} onChange={(event) => setManualWorkMode(event.target.value)} placeholder="remote" /></label>
            <label>Idiomas, separados por vírgula<input value={manualLanguages} onChange={(event) => setManualLanguages(event.target.value)} placeholder="English" /></label>
            <button type="submit">Salvar e avaliar vaga</button>
          </form>
        </section>
      ) : tab === "queue" ? (
        <section className="workspace">
          <div className="queue-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Fila de oportunidades</p>
                <h2>{jobs.length} vagas visíveis</h2>
              </div>
              <button className="secondary" onClick={() => void loadQueue()}>Atualizar</button>
            </div>
            <div className="filters">
              <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as JobStatus | '')}><option value="">Todos</option>{statuses.map((item) => <option key={item} value={item}>{formatStatus(item)}</option>)}</select></label>
              <label>Recomendação<select value={recommendation} onChange={(event) => setRecommendation(event.target.value)}><option value="">Todas</option><option value="apply">Aplicar</option><option value="review">Revisar</option><option value="skip">Pular</option></select></label>
              <label>Score mínimo<input type="number" min="0" max="100" value={minScore} onChange={(event) => setMinScore(event.target.value)} placeholder="0" /></label>
            </div>
            {loading ? <p className="empty">Carregando vagas…</p> : <div className="job-list">{jobs.map((job) => <button key={job.id} className={`job-row ${selectedJob?.id === job.id ? 'selected' : ''}`} onClick={() => void selectJob(job)}><span><strong>{job.title}</strong><small>{job.company}</small></span><span className="score">{job.score ?? '—'}</span><span className={`status ${job.status}`}>{formatStatus(job.status)}</span></button>)}</div>}
          </div>

          <aside className="detail-panel" aria-live="polite">
            {selectedJob ? <>
              <div className="detail-heading"><div><p className="eyebrow">Detalhe da vaga</p><h2>{selectedJob.title}</h2><p>{selectedJob.company}</p></div><a href={selectedJob.url} target="_blank">Abrir vaga ↗</a></div>
              <div className="metrics"><div><small>Score</small><strong>{selectedJob.score ?? '—'}</strong></div><div><small>Status</small><strong>{formatStatus(selectedJob.status)}</strong></div><div><small>Recomendação</small><strong>{selectedJob.recommendation ? formatRecommendation(selectedJob.recommendation) : '—'}</strong></div></div><h3>Dossiê de estudo</h3><div className="dossier-summary"><span><strong>Perfil em foco:</strong> {focusProfile?.name ?? "Não informado"}</span><span><strong>Senioridade:</strong> {selectedJob.seniority ?? "Não informada"}</span><span><strong>Modalidade:</strong> {selectedJob.work_mode ?? "Não informada"}</span>{selectedJob.languages.length > 0 && <span><strong>Idiomas:</strong> {selectedJob.languages.join(", ")}</span>}</div>
              <h3>Requisitos</h3><div className="chips">{[...selectedJob.required_skills, ...selectedJob.required_technologies].length > 0 ? [...selectedJob.required_skills, ...selectedJob.required_technologies].map((skill) => <span key={skill}>{skill}</span>) : <span>Não informado</span>}</div>{selectedJob.responsibilities.length > 0 && <><h3>Responsabilidades</h3><ul>{selectedJob.responsibilities.map((item) => <li key={item}>{item}</li>)}</ul></>}
              {selectedJob.desired_technologies.length > 0 && <><h3>Tecnologias desejáveis</h3><div className="chips">{selectedJob.desired_technologies.map((technology) => <span key={technology}>{technology}</span>)}</div></>}
              {latestEvaluation && <><h3>Última avaliação</h3><ul>{latestEvaluation.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>{latestEvaluation.missing_requirements.length > 0 && <p className="warning">Lacunas: {latestEvaluation.missing_requirements.join(', ')}</p>}</>}
              <h3>Anotações</h3><form className="note-form" onSubmit={(event) => void saveJobNote(event)}><textarea value={noteContent} onChange={(event) => setNoteContent(event.target.value)} placeholder="Registre observações, perguntas e próximos passos" /><div className="actions"><button type="submit">{editingNoteId ? "Salvar alteração" : "Adicionar anotação"}</button>{editingNoteId && <button type="button" className="secondary" onClick={() => { setEditingNoteId(null); setNoteContent("") }}>Cancelar</button>}</div></form>{notes.length > 0 && <div className="note-list">{notes.map((note) => <button key={note.id} type="button" onClick={() => { setEditingNoteId(note.id); setNoteContent(note.content) }}><span>{note.content}</span><small>Atualizada em {new Date(note.updated_at).toLocaleString()}</small></button>)}</div>}
              {evaluations.length > 0 && <><h3>Histórico de avaliações</h3><div className="evaluation-history">{evaluations.map((evaluation) => <div key={evaluation.id}><strong>{evaluation.score} · {formatRecommendation(evaluation.recommendation)}</strong><small>{new Date(evaluation.evaluated_at).toLocaleString()}</small><span>{evaluation.matched_skills.join(', ') || 'Sem skills identificadas'}</span></div>)}</div></>}
              <div className="actions">{selectedJob.status === 'discovered' && <button onClick={() => void evaluateJob()}>Avaliar vaga</button>}{selectedJob.status === 'evaluated' && <button onClick={() => void changeStatus('interest')}>Marcar interesse</button>}{selectedJob.status === 'interested' && <button onClick={() => void changeStatus('apply')}>Registrar candidatura</button>}{nextStatuses[selectedJob.status].length > 0 && <label>Próxima etapa<select value="" onChange={(event) => event.target.value && void changeStatus(event.target.value as JobStatus)}><option value="">Selecionar</option>{nextStatuses[selectedJob.status].map((item) => <option key={item} value={item}>{formatStatus(item)}</option>)}</select></label>}</div>
            </> : <p className="empty">Selecione uma vaga para ver seus detalhes e ações.</p>}
          </aside>
        </section>
      ) : <section className="profile-panel"><div className="section-heading"><div><p className="eyebrow">Perfil profissional</p><h2>Base para suas avaliações</h2></div><button className="secondary" onClick={() => { setSelectedProfileId(null); setProfileName(''); setSkills(''); setTargetTitles(''); setDesiredSeniority(''); setWorkModes(''); setLocations(''); setTimezones(''); setSalaryMin(''); setSalaryMax(''); setLanguages(''); setRequiredTechnologies(''); setDesiredTechnologies('') }}>Novo perfil</button></div><p className="hint">Use a Base profissional para currículo e histórico; este formulário define o recorte para a candidatura.</p><div className="profile-layout"><div className="profile-list">{profiles.map((profile) => <button key={profile.id} className={selectedProfileId === profile.id ? 'selected' : ''} onClick={() => selectProfile(profile)}><strong>{profile.name}</strong><small>{profile.target_titles.join(', ') || 'Sem cargos definidos'}</small></button>)}</div><form onSubmit={(event) => void saveProfile(event)}><label>Nome do perfil<input value={profileName} onChange={(event) => setProfileName(event.target.value)} placeholder="Tech Lead — Plataforma" /></label><label>Skills separadas por vírgula<textarea value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, FastAPI, SQLAlchemy" /></label><label>Cargos-alvo separados por vírgula<textarea value={targetTitles} onChange={(event) => setTargetTitles(event.target.value)} placeholder="Backend Engineer, Platform Engineer" /></label><label>Senioridade desejada<input value={desiredSeniority} onChange={(event) => setDesiredSeniority(event.target.value)} placeholder="Senior" /></label><label>Modalidades aceitas, separadas por vírgula<input value={workModes} onChange={(event) => setWorkModes(event.target.value)} placeholder="remote, hybrid" /></label><label>Localizações aceitas, separadas por vírgula<input value={locations} onChange={(event) => setLocations(event.target.value)} placeholder="Brazil, São Paulo" /></label><label>Fusos aceitos, separados por vírgula<input value={timezones} onChange={(event) => setTimezones(event.target.value)} placeholder="America/Sao_Paulo" /></label><label>Faixa salarial mínima<input type="number" min="0" value={salaryMin} onChange={(event) => setSalaryMin(event.target.value)} /></label><label>Faixa salarial máxima<input type="number" min="0" value={salaryMax} onChange={(event) => setSalaryMax(event.target.value)} /></label><label>Idiomas, separados por vírgula<input value={languages} onChange={(event) => setLanguages(event.target.value)} placeholder="English, Portuguese" /></label><label>Tecnologias obrigatórias, separadas por vírgula<textarea value={requiredTechnologies} onChange={(event) => setRequiredTechnologies(event.target.value)} placeholder="Python, FastAPI" /></label><label>Tecnologias desejáveis, separadas por vírgula<textarea value={desiredTechnologies} onChange={(event) => setDesiredTechnologies(event.target.value)} placeholder="Docker, Kubernetes" /></label><button type="submit">Salvar perfil</button></form></div></section>}
    </main>
  )
}

export default App
