import { useCallback, useEffect, useState } from 'react'

import {
  confirmResumeExtraction,
  createProfile,
  extractResume,
  getJobEvaluations,
  evaluateSavedJob,
  getProfiles,
  getQueue,
  moveJob,
  updateJobStatus,
  updateProfile,
} from './api'
import type { Evaluation, JobQueueItem, JobStatus, Profile, ResumeExtraction } from './types'
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

function formatStatus(status: string): string {
  return status.replaceAll('_', ' ')
}

function App() {
  const [tab, setTab] = useState<'queue' | 'profile'>('queue')
  const [jobs, setJobs] = useState<JobQueueItem[]>([])
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedJob, setSelectedJob] = useState<JobQueueItem | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [status, setStatus] = useState<JobStatus | ''>('')
  const [recommendation, setRecommendation] = useState('')
  const [minScore, setMinScore] = useState('')
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null)
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
  const [resumeContent, setResumeContent] = useState('')
  const [resumeExtraction, setResumeExtraction] = useState<ResumeExtraction | null>(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

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
      if (data.length && selectedProfileId === null) selectProfile(data[0])
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Erro ao carregar perfis.')
    }
  }, [selectedProfileId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQueue()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQueue])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadProfiles()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadProfiles])

  async function selectJob(job: JobQueueItem) {
    setSelectedJob(job)
    try {
      setEvaluations(await getJobEvaluations(job.id))
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Erro ao carregar detalhes.')
    }
  }

  function selectProfile(profile: Profile) {
    setSelectedProfileId(profile.id)
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

  async function extractResumeText() {
    try {
      const extraction = await extractResume(resumeContent)
      setResumeExtraction(extraction)
      setSkills(extraction.draft.skills.join(', '))
      setTargetTitles(extraction.draft.target_titles.join(', '))
      setLanguages(extraction.draft.languages.join(', '))
      setMessage('Rascunho extraído. Revise os campos antes de salvar.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível extrair o currículo.')
    }
  }

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = profileData()
    try {
      const profile = resumeExtraction
        ? await confirmResumeExtraction(resumeExtraction.id, {
            profile: data,
            experiences: resumeExtraction.draft.experiences,
            education: resumeExtraction.draft.education,
          })
        : selectedProfileId
        ? await updateProfile(selectedProfileId, data)
        : await createProfile(data)
      await loadProfiles()
      selectProfile(profile)
      setResumeExtraction(null)
      setMessage('Perfil salvo.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível salvar o perfil.')
    }
  }

  const latestEvaluation = evaluations[0]

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">JFinder</p>
          <h1>Seu processo seletivo, em uma só fila.</h1>
        </div>
        <nav aria-label="Navegação principal">
          <button className={tab === 'queue' ? 'active' : ''} onClick={() => setTab('queue')}>Vagas</button>
          <button className={tab === 'profile' ? 'active' : ''} onClick={() => setTab('profile')}>Perfil</button>
        </nav>
      </header>

      {message && <p className="message" role="status">{message}</p>}

      {tab === 'queue' ? (
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
              <div className="metrics"><div><small>Score</small><strong>{selectedJob.score ?? '—'}</strong></div><div><small>Status</small><strong>{formatStatus(selectedJob.status)}</strong></div><div><small>Recomendação</small><strong>{selectedJob.recommendation ?? '—'}</strong></div></div>
              <h3>Requisitos</h3><div className="chips">{selectedJob.required_skills.length > 0 ? selectedJob.required_skills.map((skill) => <span key={skill}>{skill}</span>) : <span>Não informado</span>}</div>
              {latestEvaluation && <><h3>Última avaliação</h3><ul>{latestEvaluation.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>{latestEvaluation.missing_requirements.length > 0 && <p className="warning">Lacunas: {latestEvaluation.missing_requirements.join(', ')}</p>}</>}
              {evaluations.length > 0 && <><h3>Histórico de avaliações</h3><div className="evaluation-history">{evaluations.map((evaluation) => <div key={evaluation.id}><strong>{evaluation.score} · {evaluation.recommendation}</strong><small>{new Date(evaluation.evaluated_at).toLocaleString()}</small><span>{evaluation.matched_skills.join(', ') || 'Sem skills identificadas'}</span></div>)}</div></>}
              <div className="actions">{selectedJob.status === 'discovered' && <button onClick={() => void evaluateJob()}>Avaliar vaga</button>}{selectedJob.status === 'evaluated' && <button onClick={() => void changeStatus('interest')}>Marcar interesse</button>}{selectedJob.status === 'interested' && <button onClick={() => void changeStatus('apply')}>Registrar candidatura</button>}{nextStatuses[selectedJob.status].length > 0 && <label>Próxima etapa<select value="" onChange={(event) => event.target.value && void changeStatus(event.target.value as JobStatus)}><option value="">Selecionar</option>{nextStatuses[selectedJob.status].map((item) => <option key={item} value={item}>{formatStatus(item)}</option>)}</select></label>}</div>
            </> : <p className="empty">Selecione uma vaga para ver seus detalhes e ações.</p>}
          </aside>
        </section>
      ) : <section className="profile-panel"><div className="section-heading"><div><p className="eyebrow">Perfil profissional</p><h2>Base para suas avaliações</h2></div><button className="secondary" onClick={() => { setSelectedProfileId(null); setSkills(''); setTargetTitles(''); setDesiredSeniority(''); setWorkModes(''); setLocations(''); setTimezones(''); setSalaryMin(''); setSalaryMax(''); setLanguages(''); setRequiredTechnologies(''); setDesiredTechnologies(''); setResumeExtraction(null); setResumeContent('') }}>Novo perfil</button></div><div className="resume-import"><label>Currículo em texto<textarea value={resumeContent} onChange={(event) => setResumeContent(event.target.value)} placeholder="Cole aqui o conteúdo do currículo" /></label><button type="button" className="secondary" onClick={() => void extractResumeText()}>Extrair rascunho</button>{resumeExtraction && <div className="resume-draft"><strong>Rascunho pronto para revisão</strong><span>Experiências: {resumeExtraction.draft.experiences.join(' · ') || 'Não identificadas'}</span><span>Formação: {resumeExtraction.draft.education.join(' · ') || 'Não identificada'}</span><small>Os campos do perfil foram preenchidos; revise-os e salve para confirmar.</small></div>}</div><div className="profile-layout"><div className="profile-list">{profiles.map((profile) => <button key={profile.id} className={selectedProfileId === profile.id ? 'selected' : ''} onClick={() => selectProfile(profile)}><strong>Perfil #{profile.id}</strong><small>{profile.target_titles.join(', ') || 'Sem cargos definidos'}</small></button>)}</div><form onSubmit={(event) => void saveProfile(event)}><label>Skills separadas por vírgula<textarea value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, FastAPI, SQLAlchemy" /></label><label>Cargos-alvo separados por vírgula<textarea value={targetTitles} onChange={(event) => setTargetTitles(event.target.value)} placeholder="Backend Engineer, Platform Engineer" /></label><label>Senioridade desejada<input value={desiredSeniority} onChange={(event) => setDesiredSeniority(event.target.value)} placeholder="Senior" /></label><label>Modalidades aceitas, separadas por vírgula<input value={workModes} onChange={(event) => setWorkModes(event.target.value)} placeholder="remote, hybrid" /></label><label>Localizações aceitas, separadas por vírgula<input value={locations} onChange={(event) => setLocations(event.target.value)} placeholder="Brazil, São Paulo" /></label><label>Fusos aceitos, separados por vírgula<input value={timezones} onChange={(event) => setTimezones(event.target.value)} placeholder="America/Sao_Paulo" /></label><label>Faixa salarial mínima<input type="number" min="0" value={salaryMin} onChange={(event) => setSalaryMin(event.target.value)} /></label><label>Faixa salarial máxima<input type="number" min="0" value={salaryMax} onChange={(event) => setSalaryMax(event.target.value)} /></label><label>Idiomas, separados por vírgula<input value={languages} onChange={(event) => setLanguages(event.target.value)} placeholder="English, Portuguese" /></label><label>Tecnologias obrigatórias, separadas por vírgula<textarea value={requiredTechnologies} onChange={(event) => setRequiredTechnologies(event.target.value)} placeholder="Python, FastAPI" /></label><label>Tecnologias desejáveis, separadas por vírgula<textarea value={desiredTechnologies} onChange={(event) => setDesiredTechnologies(event.target.value)} placeholder="Docker, Kubernetes" /></label><button type="submit">Salvar perfil</button></form></div></section>}
    </main>
  )
}

export default App
