import { useEffect, useRef, useState } from "react"

type Screen = "monitor" | "stats" | "exercises"

const EyeIcon = ({ closed = false }: { closed?: boolean }) => (
  <svg aria-hidden="true" viewBox="0 0 24 24">
    {closed ? (
      <path d="M3.5 13.5c2.2-1.8 5-2.7 8.5-2.7s6.3.9 8.5 2.7M8.5 11.4l-1-2M15.5 11.4l1-2" />
    ) : (
      <>
        <path d="M2.5 12s3.5-5.2 9.5-5.2 9.5 5.2 9.5 5.2-3.5 5.2-9.5 5.2S2.5 12 2.5 12Z" />
        <circle cx="12" cy="12" r="2.6" />
      </>
    )}
  </svg>
)

const Icon = ({
  name,
}: {
  name: "sun" | "thermo" | "clock" | "blink" | "camera" | "pause" | "play" | "chart" | "arrow" | "download"
}) => {
  const paths = {
    sun: (
      <>
        <circle cx="12" cy="12" r="3.5" />
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
      </>
    ),
    thermo: (
      <>
        <path d="M9 14.8V5a3 3 0 0 1 6 0v9.8a5 5 0 1 1-6 0Z" />
        <path d="M12 8v9" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3.5 2" />
      </>
    ),
    blink: <EyeIcon />,
    camera: (
      <>
        <path d="M4 7.5h3l1.5-2h7l1.5 2h3a2 2 0 0 1 2 2v8.5a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9.5a2 2 0 0 1 2-2Z" />
        <circle cx="12" cy="13.5" r="4" />
      </>
    ),
    pause: (
      <>
        <path d="M8 6v12M16 6v12" />
      </>
    ),
    play: <path d="m9 6 9 6-9 6Z" />,
    chart: (
      <>
        <path d="M4 19V10M10 19V5M16 19v-7M22 19V8" />
        <path d="M2 19h21" />
      </>
    ),
    arrow: <path d="m14 6-6 6 6 6" />,
    download: (
      <>
        <path d="M12 3v12M7 10l5 5 5-5" />
        <path d="M4 19v2h16v-2" />
      </>
    ),
  }
  return (
    <svg aria-hidden="true" className="icon" viewBox="0 0 24 24">
      {paths[name]}
    </svg>
  )
}

function WindowBar() {
  return (
    <header className="window-bar">
      <div className="brand">
        <span className="brand-mark">
          <EyeIcon />
        </span>
        <strong>Blinky</strong>
        <span className="brand-separator" />
        <span>Monitor de fatiga ocular</span>
      </div>
      <div className="window-controls" aria-label="Controles de ventana">
        <button aria-label="Minimizar">
          <img src="/assets/575f0.svg" alt="" />
        </button>
        <button aria-label="Restaurar">
          <img src="/assets/7c7f0.svg" alt="" />
        </button>
        <button aria-label="Cerrar">
          <img src="/assets/061c7.svg" alt="" />
        </button>
      </div>
    </header>
  )
}

function StatusPill({ label, ok = true }: { label: string ok?: boolean }) {
  return (
    <span className={`status-pill ${ok ? "ok" : "warning"}`}>
      <i />
      {label}
    </span>
  )
}

function Monitor({
  onStats,
  onExercises,
}: {
  onStats: () => void
  onExercises: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [cameraOn, setCameraOn] = useState(false)
  const [cameraError, setCameraError] = useState(false)
  const [running, setRunning] = useState(true)
  const [seconds, setSeconds] = useState(1524)
  const [blinks, setBlinks] = useState(248)
  const [eyesClosed, setEyesClosed] = useState(false)
  const [notice, setNotice] = useState(true)

  useEffect(() => {
    if (!running) return
    const timer = window.setInterval(() => {
      setSeconds((value) => value + 1)
      if (Math.random() > 0.89) {
        setEyesClosed(true)
        window.setTimeout(() => {
          setEyesClosed(false)
          setBlinks((value) => value + 1)
        }, 180)
      }
    }, 1000)
    return () => window.clearInterval(timer)
  }, [running])

  useEffect(
    () => () => streamRef.current?.getTracks().forEach((track) => track.stop()),
    [],
  )

  const toggleCamera = async () => {
    if (cameraOn) {
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      setCameraOn(false)
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCameraError(false)
      setCameraOn(true)
    } catch {
      setCameraError(true)
    }
  }

  const duration = `${String(Math.floor(seconds / 3600)).padStart(2, "0")}:${String(Math.floor((seconds % 3600) / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`

  return (
    <main className="app-content monitor-screen">
      <section className="monitor-heading">
        <div>
          <p className="eyebrow">SESIÓN ACTIVA</p>
          <h1>Buenos días, Alex</h1>
          <p>Blinky está cuidando tu salud visual mientras trabajas.</p>
        </div>
        <StatusPill
          label={running ? "Monitoreo en curso" : "Monitoreo pausado"}
          ok={running}
        />
      </section>

      <div className="monitor-grid">
        <section className="camera-card">
          <div className="card-topline">
            <div>
              <h2>Cámara en vivo</h2>
              <span>Detección facial local</span>
            </div>
            <button className="ghost-button" onClick={toggleCamera}>
              <Icon name="camera" />{" "}
              {cameraOn ? "Apagar cámara" : "Activar cámara"}
            </button>
          </div>
          <div className={`camera-feed ${cameraOn ? "is-on" : ""}`}>
            <video ref={videoRef} autoPlay muted playsInline />
            {!cameraOn && (
              <div className="camera-placeholder">
                <span className="camera-icon-source">
                  <img src="/assets/0eb9a.svg" alt="" />
                </span>
                <strong>
                  {cameraError
                    ? "No se pudo acceder a la cámara"
                    : "La cámara está desactivada"}
                </strong>
                <p>
                  {cameraError
                    ? "Revisa los permisos de cámara del navegador."
                    : "Actívala para comenzar la detección ocular."}
                </p>
                <button
                  className="primary-button compact"
                  onClick={toggleCamera}
                >
                  Activar cámara
                </button>
              </div>
            )}
            <div className="camera-overlay">
              <span>
                <i /> {cameraOn ? "CÁMARA CONECTADA" : "CÁMARA EN ESPERA"}
              </span>
              <span>720p · 30 FPS</span>
            </div>
            {cameraOn && (
              <div className="face-guide">
                <span>Rostro detectado</span>
              </div>
            )}
          </div>
          <div className="sensor-strip">
            <span>
              <i /> Cámara <b>{cameraOn ? "Activa" : "En espera"}</b>
            </span>
            <span>
              <i /> Sensor ambiental <b>Conectado</b>
            </span>
            <span>
              <i /> Detección facial <b>{cameraOn ? "Activa" : "En espera"}</b>
            </span>
          </div>
        </section>

        <aside className="side-panel">
          <section className="eye-card">
            <div className="card-topline">
              <div>
                <h2>Estado de los ojos</h2>
                <span>Actualizado ahora</span>
              </div>
              <StatusPill label="Normal" />
            </div>
            <div className="eyes-visual">
              <div>
                <EyeIcon closed={eyesClosed} />
              </div>
              <div>
                <EyeIcon closed={eyesClosed} />
              </div>
            </div>
            <div className="eye-labels">
              <span>
                Ojo izquierdo <b>{eyesClosed ? "Cerrado" : "Abierto"}</b>
              </span>
              <span>
                Ojo derecho <b>{eyesClosed ? "Cerrado" : "Abierto"}</b>
              </span>
            </div>
          </section>

          <section className="metrics-card">
            <div className="card-topline">
              <div>
                <h2>Métricas de sesión</h2>
                <span>Datos en tiempo real</span>
              </div>
            </div>
            <div className="metric-grid">
              <article>
                <span className="metric-icon violet">
                  <Icon name="blink" />
                </span>
                <div>
                  <small>PARPADEOS</small>
                  <strong>{blinks}</strong>
                  <em>12 por minuto</em>
                </div>
              </article>
              <article>
                <span className="metric-icon orange">
                  <Icon name="thermo" />
                </span>
                <div>
                  <small>TEMPERATURA</small>
                  <strong>
                    23.4<span>°C</span>
                  </strong>
                  <em>Óptima</em>
                </div>
              </article>
              <article>
                <span className="metric-icon yellow">
                  <Icon name="sun" />
                </span>
                <div>
                  <small>ILUMINACIÓN</small>
                  <strong>
                    420<span> lux</span>
                  </strong>
                  <em>Adecuada</em>
                </div>
              </article>
              <article>
                <span className="metric-icon blue">
                  <Icon name="clock" />
                </span>
                <div>
                  <small>TIEMPO ACTIVO</small>
                  <strong className="timer">{duration}</strong>
                  <em>Sesión actual</em>
                </div>
              </article>
            </div>
          </section>

          <button className="stats-button" onClick={onStats}>
            <span>
              <Icon name="chart" />
            </span>
            <div>
              <strong>Ver estadísticas</strong>
              <small>Consulta tu progreso y tendencias</small>
            </div>
            <b>→</b>
          </button>
        </aside>
      </div>

      {notice && (
        <section className="fatigue-alert" role="alert">
          <span className="fatigue-alert-icon">
            <EyeIcon closed />
          </span>
          <div>
            <span className="alert-kicker">FATIGA VISUAL DETECTADA</span>
            <strong>Tus ojos necesitan una pausa</strong>
            <p>
              Detectamos una disminución en tu frecuencia de parpadeo. Una
              rutina breve puede ayudarte a relajar la vista.
            </p>
          </div>
          <div className="fatigue-actions">
            <button className="alert-dismiss" onClick={() => setNotice(false)}>
              Ahora no
            </button>
            <button className="alert-action" onClick={onExercises}>
              Ver ejercicios <b>→</b>
            </button>
          </div>
        </section>
      )}

      <footer className="session-footer">
        <div>
          <span className="pulse-dot" />
          <p>
            <strong>Todo funciona correctamente</strong>
            <small>Última comprobación hace 12 segundos</small>
          </p>
        </div>
        <button
          className={running ? "pause-button" : "primary-button"}
          onClick={() => setRunning((value) => !value)}
        >
          <Icon name={running ? "pause" : "play"} />{" "}
          {running ? "Pausar monitoreo" : "Reanudar monitoreo"}
        </button>
      </footer>
    </main>
  )
}

function Stats({ onBack }: { onBack: () => void }) {
  const [range, setRange] = useState("Semana")
  const bars = [48, 56, 42, 68, 59, 76, 63]
  const download = () => {
    const rows = [
      "dia,parpadeos,fatiga",
      "Lun,251,18",
      "Mar,267,22",
      "Mie,239,16",
      "Jue,284,29",
      "Vie,272,24",
      "Sab,301,31",
      "Dom,248,20",
    ]
    const link = document.createElement("a")
    link.href = URL.createObjectURL(
      new Blob([rows.join("\n")], { type: "text/csv" }),
    )
    link.download = "blinky-estadisticas.csv"
    link.click()
    URL.revokeObjectURL(link.href)
  }
  return (
    <main className="app-content stats-screen">
      <section className="stats-heading">
        <div className="back-title">
          <button className="back-button" onClick={onBack}>
            <Icon name="arrow" />
          </button>
          <div>
            <p className="eyebrow">RESUMEN DE BIENESTAR</p>
            <h1>Tus estadísticas</h1>
            <p>Conoce tus hábitos visuales y cómo han evolucionado.</p>
          </div>
        </div>
        <div className="heading-actions">
          <div className="range-control">
            {["Hoy", "Semana", "Mes"].map((item) => (
              <button
                className={range === item ? "active" : ""}
                onClick={() => setRange(item)}
                key={item}
              >
                {item}
              </button>
            ))}
          </div>
          <button className="primary-button" onClick={download}>
            <Icon name="download" /> Descargar CSV
          </button>
        </div>
      </section>

      <section className="summary-grid">
        <article>
          <span className="metric-icon violet">
            <Icon name="blink" />
          </span>
          <div>
            <small>PARPADEOS TOTALES</small>
            <strong>1,862</strong>
            <em>↑ 8% vs. semana anterior</em>
          </div>
        </article>
        <article>
          <span className="metric-icon blue">
            <Icon name="clock" />
          </span>
          <div>
            <small>TIEMPO MONITOREADO</small>
            <strong>21h 34m</strong>
            <em>6 sesiones registradas</em>
          </div>
        </article>
        <article>
          <span className="metric-icon orange">
            <EyeIcon />
          </span>
          <div>
            <small>ÍNDICE DE FATIGA</small>
            <strong>
              22<span>%</span>
            </strong>
            <em>Dentro del rango saludable</em>
          </div>
        </article>
        <article>
          <span className="metric-icon yellow">
            <Icon name="sun" />
          </span>
          <div>
            <small>AMBIENTE ÓPTIMO</small>
            <strong>
              87<span>%</span>
            </strong>
            <em>Iluminación adecuada</em>
          </div>
        </article>
      </section>

      <section className="insight-banner">
        <span>i</span>
        <div>
          <strong>Tu mejor día fue el miércoles</strong>
          <p>
            Tu índice de fatiga fue 18% menor gracias a pausas más frecuentes.
          </p>
        </div>
      </section>

      <div className="charts-grid">
        <section className="chart-card">
          <div className="card-topline">
            <div>
              <h2>Parpadeos por día</h2>
              <span>Promedio: 266 parpadeos/día</span>
            </div>
            <img
              className="source-watermark bars-source"
              src="/assets/6fc72.svg"
              alt=""
            />
          </div>
          <div className="bar-chart">
            {bars.map((height, index) => (
              <div key={index}>
                <span style={{ height: `${height}%` }} />
                <small>
                  {["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][index]}
                </small>
              </div>
            ))}
          </div>
        </section>
        <section className="chart-card">
          <div className="card-topline">
            <div>
              <h2>Distribución de fatiga</h2>
              <span>Basado en 6 sesiones</span>
            </div>
            <img className="source-watermark" src="/assets/9d18b.svg" alt="" />
          </div>
          <div className="donut-layout">
            <div className="donut">
              <div>
                <strong>78%</strong>
                <span>Saludable</span>
              </div>
            </div>
            <ul>
              <li>
                <i className="green" />
                Óptimo <b>58%</b>
              </li>
              <li>
                <i className="yellow-dot" />
                Moderado <b>20%</b>
              </li>
              <li>
                <i className="red" />
                Fatiga alta <b>22%</b>
              </li>
            </ul>
          </div>
        </section>
      </div>

      <section className="history-card">
        <div className="card-topline">
          <div>
            <h2>Sesiones recientes</h2>
            <span>Historial de monitoreo</span>
          </div>
        </div>
        <div className="history-row header">
          <span>FECHA</span>
          <span>DURACIÓN</span>
          <span>PARPADEOS</span>
          <span>FATIGA</span>
          <span>ESTADO</span>
        </div>
        {[
          ["Hoy, 09:12", "25 min", "248", "20%", "Saludable"],
          ["Ayer, 14:35", "2h 18m", "284", "27%", "Moderado"],
          ["Mié, 10:08", "3h 04m", "301", "16%", "Saludable"],
        ].map((row) => (
          <div className="history-row" key={row[0]}>
            {row.map((cell, i) => (
              <span
                key={cell}
                className={
                  i === 4
                    ? cell === "Saludable"
                      ? "state-good"
                      : "state-mid"
                    : ""
                }
              >
                {cell}
              </span>
            ))}
          </div>
        ))}
      </section>
    </main>
  )
}

const exercises = [
  {
    number: "01",
    title: "Regla 20-20-20",
    duration: 20,
    tag: "RELAJACIÓN DE ENFOQUE",
    description:
      "Mira un punto situado a unos 6 metros de distancia durante 20 segundos. Esto relaja los músculos que mantienen el enfoque cercano.",
    steps: [
      "Aléjate de la pantalla",
      "Elige un objeto lejano",
      "Respira con naturalidad",
    ],
    visual: "focus",
  },
  {
    number: "02",
    title: "Palming",
    duration: 30,
    tag: "DESCANSO PROFUNDO",
    description:
      "Frota tus manos hasta calentarlas y colócalas suavemente sobre los ojos cerrados, sin ejercer presión. Disfruta de la oscuridad.",
    steps: ["Calienta tus manos", "Cierra los ojos", "Cubre sin presionar"],
    visual: "palming",
  },
]

function ExerciseVisual({ type }: { type: string }) {
  return (
    <div className={`exercise-visual ${type}`}>
      <div className="figma-placeholder-assets" aria-hidden="true">
        <img className="placeholder-rectangle" src="/assets/df018.svg" alt="" />
        <img
          className="placeholder-line first"
          src="/assets/d8cb7.svg"
          alt=""
        />
        <img
          className="placeholder-line second"
          src="/assets/a5290.svg"
          alt=""
        />
      </div>
      {type === "focus" ? (
        <>
          <span className="focus-eye">
            <EyeIcon />
          </span>
          <span className="focus-path" />
          <span className="focus-target">
            <i />
          </span>
          <small>Mantén la mirada en un punto lejano</small>
        </>
      ) : (
        <>
          <span className="palm palm-left" />
          <span className="palm palm-right" />
          <span className="resting-eyes">
            <EyeIcon closed />
          </span>
          <span className="calm-wave wave-one" />
          <span className="calm-wave wave-two" />
          <small>Sin presión, respira lentamente</small>
        </>
      )}
    </div>
  )
}

function Exercises({ onBack }: { onBack: () => void }) {
  const [selected, setSelected] = useState(0)
  const [remaining, setRemaining] = useState(exercises[0].duration)
  const [active, setActive] = useState(false)
  const [completed, setCompleted] = useState<number[]>([])
  const current = exercises[selected]

  useEffect(() => {
    setRemaining(current.duration)
    setActive(false)
  }, [current.duration, selected])

  useEffect(() => {
    if (!active) return
    if (remaining === 0) {
      setActive(false)
      setCompleted((items) =>
        items.includes(selected) ? items : [...items, selected],
      )
      return
    }
    const timer = window.setTimeout(
      () => setRemaining((value) => value - 1),
      1000,
    )
    return () => window.clearTimeout(timer)
  }, [active, remaining, selected])

  const progress = ((current.duration - remaining) / current.duration) * 100

  return (
    <main className="app-content exercises-screen">
      <section className="exercise-heading">
        <div className="back-title">
          <button className="back-button" onClick={onBack}>
            <Icon name="arrow" />
          </button>
          <div>
            <p className="eyebrow">PAUSA DE BIENESTAR</p>
            <h1>Ejercicios recomendados</h1>
            <p>Dos minutos para relajar la vista y recuperar el enfoque.</p>
          </div>
        </div>
        <div className="routine-progress">
          <span>
            {completed.length} de {exercises.length} completados
          </span>
          <div>
            <i
              style={{
                width: `${(completed.length / exercises.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </section>

      <section className="exercise-intro">
        <span className="intro-icon">
          <EyeIcon />
        </span>
        <div>
          <strong>Haz una pausa antes de continuar</strong>
          <p>
            Mantén una postura cómoda y quítate las gafas si lo necesitas. Los
            ejercicios no deben causar molestias.
          </p>
        </div>
        <span className="routine-time">
          <Icon name="clock" /> 1 min
        </span>
      </section>

      <div className="exercise-layout">
        <nav className="exercise-list" aria-label="Lista de ejercicios">
          {exercises.map((exercise, index) => (
            <button
              className={`${selected === index ? "selected" : ""} ${
                completed.includes(index) ? "completed" : ""
              }`}
              key={exercise.title}
              onClick={() => setSelected(index)}
            >
              <span>{completed.includes(index) ? "✓" : exercise.number}</span>
              <div>
                <small>{exercise.tag}</small>
                <strong>{exercise.title}</strong>
                <em>{exercise.duration} segundos</em>
              </div>
              <b>›</b>
            </button>
          ))}
          <div className="exercise-tip">
            <span>i</span>
            <p>
              <strong>Consejo Blinky</strong>
              Repite esta rutina cada 20 minutos de trabajo continuo.
            </p>
          </div>
        </nav>

        <section className="exercise-detail">
          <div className="exercise-card-heading">
            <div>
              <span>
                EJERCICIO {current.number} · {current.tag}
              </span>
              <h2>{current.title}</h2>
            </div>
            {completed.includes(selected) && <StatusPill label="Completado" />}
          </div>

          <div className="exercise-main">
            <ExerciseVisual type={current.visual} />
            <div className="exercise-copy">
              <p>{current.description}</p>
              <ol>
                {current.steps.map((step, index) => (
                  <li key={step}>
                    <span>{index + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="exercise-player">
            <div
              className="timer-ring"
              style={{ "--progress": `${progress}%` } as React.CSSProperties}
            >
              <div>
                <strong>{remaining}</strong>
                <span>seg</span>
              </div>
            </div>
            <div className="player-copy">
              <strong>
                {remaining === 0
                  ? "Ejercicio completado"
                  : active
                    ? "Sigue así, respira con calma"
                    : "Cuando estés listo, comienza"}
              </strong>
              <span>
                {active
                  ? "Blinky te avisará cuando termine el tiempo."
                  : "El monitoreo está pausado durante el ejercicio."}
              </span>
              <div className="player-progress">
                <i style={{ width: `${progress}%` }} />
              </div>
            </div>
            <button
              className="primary-button exercise-start"
              onClick={() => {
                if (remaining === 0) setRemaining(current.duration)
                setActive((value) => !value)
              }}
            >
              <Icon name={active ? "pause" : "play"} />
              {active ? "Pausar" : remaining === 0 ? "Repetir" : "Comenzar"}
            </button>
          </div>
        </section>
      </div>

      <footer className="exercise-footer">
        <p>
          <span className="pulse-dot" />
          Tu sesión de monitoreo se reanudará al volver
        </p>
        <button className="ghost-button" onClick={onBack}>
          Volver al monitoreo
        </button>
      </footer>
    </main>
  )
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("monitor")
  return (
    <div className="desktop-shell">
      <WindowBar />
      {screen === "monitor" && (
        <Monitor
          onStats={() => setScreen("stats")}
          onExercises={() => setScreen("exercises")}
        />
      )}
      {screen === "stats" && <Stats onBack={() => setScreen("monitor")} />}
      {screen === "exercises" && (
        <Exercises onBack={() => setScreen("monitor")} />
      )}
    </div>
  )
}
