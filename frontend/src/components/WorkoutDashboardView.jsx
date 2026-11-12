import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Edit3,
  Sparkles,
  RefreshCw,
  Clock,
  Calendar,
  Scale,
  Ruler,
  Dumbbell,
  Flame,
  Zap,
  Star,
  Timer,
  HeartPulse,
  Ban,
  AlertCircle,
  Info,
} from 'lucide-react';

const GOAL_LABELS = {
  EMAGRECIMENTO: { label: 'Emagrecimento', icon: Flame, color: 'text-rose-400' },
  HIPERTROFIA: { label: 'Hipertrofia', icon: Dumbbell, color: 'text-orange-400' },
  FORCA: { label: 'Treino de Força', icon: Zap, color: 'text-sky-400' },
};

const LEVEL_LABELS = {
  INICIANTE: 'Iniciante',
  INTERMEDIARIO: 'Intermediário',
  AVANCADO: 'Avançado',
};

const COMPLEXITY_STYLE = {
  BAIXA: {
    label: '🟢 Complexidade Baixa',
    classes: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  },
  MEDIA: {
    label: '🟡 Complexidade Média',
    classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  },
  ALTA: {
    label: '🔴 Complexidade Alta',
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
};

export default function WorkoutDashboardView({
  profile,
  onBackToProfiles,
  onOpenEditProfile,
  onRequestGenerateFull,
  onRequestRegenerateDay,
}) {
  const activePlan = profile?.active_workout || null;
  const days = activePlan?.days || [];
  const [selectedDayNumber, setSelectedDayNumber] = useState(1);

  useEffect(() => {
    if (days.length > 0) {
      const exists = days.some((d) => d.day_number === selectedDayNumber);
      if (!exists) {
        setSelectedDayNumber(days[0].day_number);
      }
    } else {
      setSelectedDayNumber(1);
    }
  }, [days, selectedDayNumber]);

  const currentDay = days.find((d) => d.day_number === selectedDayNumber) || days[0] || null;
  const goalMeta = GOAL_LABELS[profile.goal] || GOAL_LABELS.HIPERTROFIA;
  const GoalIcon = goalMeta.icon;

  const daysMismatch =
    activePlan && activePlan.days_per_week_snapshot !== profile.days_per_week;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      {/* Top Bar Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBackToProfiles}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white text-sm font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Trocar Perfil</span>
        </button>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => onOpenEditProfile(profile)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-sm font-medium transition-colors"
          >
            <Edit3 className="w-4 h-4 text-orange-400" />
            <span>Editar Perfil</span>
          </button>

          <button
            type="button"
            onClick={onRequestGenerateFull}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-sm font-bold transition-all shadow-lg shadow-orange-500/20"
          >
            <Sparkles className="w-4 h-4" />
            <span>
              {activePlan ? 'Gerar Todo o Treino do Zero' : 'Gerar Treinamento Completo'}
            </span>
          </button>
        </div>
      </div>

      {/* Profile Summary Card */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 sm:p-6 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                {profile.name}
              </h1>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-500/15 text-orange-400 border border-orange-500/30">
                <GoalIcon className="w-3.5 h-3.5" />
                {goalMeta.label}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
                Nível: {LEVEL_LABELS[profile.fitness_level] || profile.fitness_level}
              </span>
            </div>
            {profile.excluded_exercise_ids?.length > 0 && (
              <p className="text-xs text-rose-400 flex items-center gap-1.5 pt-1">
                <Ban className="w-3.5 h-3.5" />
                <span>
                  {profile.excluded_exercise_ids.length} exercício(s) marcado(s) para exclusão na
                  montagem
                </span>
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Scale className="w-3.5 h-3.5 text-orange-400" />
                <span>Peso</span>
              </div>
              <div className="text-base font-bold text-white mt-0.5">{profile.weight_kg} kg</div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Ruler className="w-3.5 h-3.5 text-orange-400" />
                <span>Altura</span>
              </div>
              <div className="text-base font-bold text-white mt-0.5">{profile.height_cm} cm</div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock className="w-3.5 h-3.5 text-orange-400" />
                <span>Tempo / Dia</span>
              </div>
              <div className="text-base font-bold text-white mt-0.5">
                {profile.available_time_minutes} min
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Calendar className="w-3.5 h-3.5 text-orange-400" />
                <span>Frequência</span>
              </div>
              <div className="text-base font-bold text-white mt-0.5">
                {profile.days_per_week} dias/sem
              </div>
            </div>
          </div>
        </div>

        {daysMismatch && (
          <div className="mt-4 p-3.5 rounded-xl bg-amber-500/15 border border-amber-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-amber-200 text-xs sm:text-sm">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Você alterou sua frequência para <strong>{profile.days_per_week} dias/semana</strong>,
                mas o treino atual foi gerado para{' '}
                <strong>{activePlan.days_per_week_snapshot} dias/semana</strong>.
              </span>
            </div>
            <button
              type="button"
              onClick={onRequestGenerateFull}
              className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs shrink-0"
            >
              Recriar Plano para {profile.days_per_week} Dias
            </button>
          </div>
        )}
      </div>

      {/* Empty Workout State */}
      {!activePlan ? (
        <div className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/60 p-10 sm:p-16 text-center space-y-5">
          <div className="w-16 h-16 rounded-2xl bg-orange-500/15 border border-orange-500/30 flex items-center justify-center mx-auto text-orange-400">
            <Sparkles className="w-8 h-8" />
          </div>
          <div className="space-y-2 max-w-lg mx-auto">
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              Pronto para montar seu treino personalizado?
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Antes de gerar o treino, você poderá revisar o catálogo de exercícios do banco de
              dados e excluir qualquer exercício que não deseje fazer.
            </p>
          </div>
          <button
            type="button"
            onClick={onRequestGenerateFull}
            className="inline-flex items-center gap-2.5 px-7 py-4 rounded-2xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-base transition-all shadow-xl shadow-orange-500/25"
          >
            <Sparkles className="w-5 h-5" />
            <span>Revisar Exercícios e Gerar Meu Treino</span>
          </button>
        </div>
      ) : (
        /* Active Workout Plan */
        <div className="space-y-6">
          {/* Split Header & Specialist Notes */}
          <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800/70 border border-slate-800 p-5 space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="text-xs font-bold uppercase tracking-wider text-orange-400">
                Divisão Prescrita pelo Agente LLM Especialista
              </div>
              <div className="text-xs text-slate-400">
                Pode ser gerado novamente do zero ou por dia quantas vezes você quiser
              </div>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white">{activePlan.split_name}</h2>
            {activePlan.specialist_notes && (
              <p className="text-xs sm:text-sm text-slate-300 flex items-start gap-2 pt-1">
                <Info className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                <span>{activePlan.specialist_notes}</span>
              </p>
            )}
          </div>

          {/* Day Selector Tabs (Responsive Horizontal Scroll on Mobile, Grid/Flex on Desktop) */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {days.map((day) => {
              const isSelected = currentDay?.day_number === day.day_number;
              return (
                <button
                  key={day.id}
                  type="button"
                  onClick={() => setSelectedDayNumber(day.day_number)}
                  className={`px-4 py-3 rounded-xl font-bold text-sm whitespace-nowrap border transition-all flex items-center gap-2 ${
                    isSelected
                      ? 'bg-orange-500 border-orange-500 text-white shadow-lg shadow-orange-500/20'
                      : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white'
                  }`}
                >
                  <span>Dia {day.day_number}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-md ${
                      isSelected ? 'bg-black/25 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {day.estimated_duration_minutes} min
                  </span>
                </button>
              );
            })}
          </div>

          {/* Selected Day Content */}
          {currentDay && (
            <div className="space-y-5">
              {/* Day Header + Regenerate Single Day Button */}
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-orange-500/20 text-orange-300 border border-orange-500/30">
                      DIA {currentDay.day_number} DE {days.length}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-orange-400" />
                      Duração total estimada: {currentDay.estimated_duration_minutes} min (Limite:{' '}
                      {profile.available_time_minutes} min)
                    </span>
                  </div>
                  <h3 className="text-xl font-extrabold text-white">{currentDay.day_title}</h3>
                  <p className="text-xs sm:text-sm text-slate-400">
                    Músculos trabalhados: <strong className="text-slate-200">{currentDay.target_muscles}</strong>
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => onRequestRegenerateDay(currentDay.day_number)}
                  className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-orange-500 border border-slate-700 hover:border-orange-500 text-white font-semibold text-xs sm:text-sm transition-all shrink-0"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Gerar Novo Treino Apenas para o Dia {currentDay.day_number}</span>
                </button>
              </div>

              {/* Cardio Block (Strictly showing ONLY time, e.g., "40 min de cardio") */}
              <div className="rounded-2xl bg-gradient-to-r from-emerald-950/50 via-slate-900 to-slate-900 border border-emerald-500/30 p-5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                    <HeartPulse className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      Exercício Cardiovascular Prescrito
                    </div>
                    <div
                      data-testid="cardio-display-text"
                      className="text-xl sm:text-2xl font-extrabold text-white mt-0.5"
                    >
                      {currentDay.cardio_display_text}
                    </div>
                  </div>
                </div>
              </div>

              {/* Lifting Exercises List */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 px-1">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                    Exercícios de Musculação ({currentDay.exercises.length})
                  </h4>
                  <span className="text-xs text-slate-400">
                    Ordenados por grupo muscular (maior → menor), complexidade e eficiência
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-3.5">
                  {currentDay.exercises.map((ex, idx) => {
                    const comp = COMPLEXITY_STYLE[ex.complexity] || COMPLEXITY_STYLE.MEDIA;
                    const prevGroup = idx > 0 ? currentDay.exercises[idx - 1].muscle_group : null;
                    const isNewMuscleGroupBlock = ex.muscle_group !== prevGroup;
                    const blockNumber = currentDay.exercises
                      .slice(0, idx + 1)
                      .reduce((acc, item, i, arr) => {
                        if (i === 0 || item.muscle_group !== arr[i - 1].muscle_group) {
                          return acc + 1;
                        }
                        return acc;
                      }, 0);

                    return (
                      <React.Fragment
                        key={`${currentDay.id}-${ex.execution_order}-${ex.exercise_id}`}
                      >
                        {isNewMuscleGroupBlock && (
                          <div className="pt-2 first:pt-0 flex items-center gap-2.5">
                            <span className="px-2.5 py-1 rounded-lg text-xs font-extrabold uppercase tracking-wider bg-orange-500/15 text-orange-400 border border-orange-500/30">
                              {blockNumber}º Bloco: {ex.muscle_group}
                            </span>
                            <div className="h-px flex-1 bg-slate-800/80" />
                          </div>
                        )}
                        <div className="rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 sm:p-5 transition-all">
                        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                          <div className="flex items-start gap-3.5">
                            <div className="w-9 h-9 rounded-xl bg-orange-500/15 border border-orange-500/30 text-orange-400 font-extrabold text-sm flex items-center justify-center shrink-0 mt-0.5">
                              #{ex.execution_order}
                            </div>
                            <div className="space-y-1.5">
                              <div className="flex items-center gap-2.5 flex-wrap">
                                <h5 className="text-base sm:text-lg font-bold text-white">
                                  {ex.popular_name}
                                </h5>
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${comp.classes}`}
                                >
                                  {comp.label}
                                </span>
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-slate-950 text-amber-300 border border-slate-800">
                                  <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                                  Eficiência {ex.efficiency_score.toFixed(1)}/10
                                </span>
                              </div>

                              <div className="text-xs text-slate-400 space-x-2">
                                <span>
                                  <strong className="text-slate-300">Grupo:</strong> {ex.muscle_group}
                                </span>
                                <span>•</span>
                                <span>
                                  <strong className="text-slate-300">Principal:</strong>{' '}
                                  {ex.primary_muscle}
                                </span>
                                {ex.secondary_muscles && (
                                  <>
                                    <span>•</span>
                                    <span>
                                      <strong className="text-slate-300">Secundários:</strong>{' '}
                                      {ex.secondary_muscles}
                                    </span>
                                  </>
                                )}
                              </div>

                              {ex.execution_notes && (
                                <p className="text-xs text-slate-300 bg-slate-950/70 border border-slate-800/80 rounded-lg px-3 py-1.5 inline-block">
                                  💡 {ex.execution_notes}
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Sets, Reps & Rest */}
                          <div className="grid grid-cols-3 gap-2.5 sm:w-auto lg:shrink-0 border-t lg:border-t-0 border-slate-800 pt-3 lg:pt-0">
                            <div className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-center">
                              <div className="text-[11px] uppercase tracking-wider text-slate-400">
                                Séries
                              </div>
                              <div className="text-base sm:text-lg font-extrabold text-orange-400">
                                {ex.sets}x
                              </div>
                            </div>

                            <div className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-center">
                              <div className="text-[11px] uppercase tracking-wider text-slate-400">
                                Repetições
                              </div>
                              <div className="text-base sm:text-lg font-extrabold text-white">
                                {ex.reps}
                              </div>
                            </div>

                            <div className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-center">
                              <div className="text-[11px] uppercase tracking-wider text-slate-400 flex items-center justify-center gap-1">
                                <Timer className="w-3 h-3 text-slate-400" />
                                <span>Descanso</span>
                              </div>
                              <div className="text-base sm:text-lg font-extrabold text-slate-200">
                                {ex.rest_seconds}s
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
