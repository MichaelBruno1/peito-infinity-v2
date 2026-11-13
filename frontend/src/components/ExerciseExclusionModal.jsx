import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  X,
  Search,
  Sparkles,
  CheckCircle2,
  Ban,
  Filter,
  RotateCcw,
  Star,
  RefreshCw,
} from 'lucide-react';

const COMPLEXITY_BADGE = {
  BAIXA: { label: '🟢 Baixa', classes: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  MEDIA: { label: '🟡 Média', classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  ALTA: { label: '🔴 Alta', classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
};

const EMPTY_IDS = [];

export default function ExerciseExclusionModal({
  isOpen,
  onClose,
  onConfirmGenerate,
  exerciseCatalog,
  isLoadingExercises = false,
  onRetryLoadExercises,
  profileId = null,
  initialExcludedIds = EMPTY_IDS,
  generationMode = 'FULL', // 'FULL' | 'SINGLE_DAY'
  targetDayNumber = null,
  isGenerating = false,
}) {
  const [excludedSet, setExcludedSet] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('ALL');
  const [selectedComplexity, setSelectedComplexity] = useState('ALL');
  const [errorMsg, setErrorMsg] = useState('');
  const wasOpenRef = useRef(false);
  const lastProfileIdRef = useRef(null);

  useEffect(() => {
    if (isOpen && (!wasOpenRef.current || lastProfileIdRef.current !== profileId)) {
      setExcludedSet(new Set(initialExcludedIds || []));
      setSearchQuery('');
      setSelectedGroup('ALL');
      setSelectedComplexity('ALL');
      setErrorMsg('');
      if (!exerciseCatalog?.groups?.length && onRetryLoadExercises) {
        onRetryLoadExercises();
      }
    }
    wasOpenRef.current = isOpen;
    lastProfileIdRef.current = profileId;
  }, [isOpen, profileId, initialExcludedIds, exerciseCatalog, onRetryLoadExercises]);

  const groups = exerciseCatalog?.groups || [];
  const totalExercises = exerciseCatalog?.total || 0;

  const filteredGroups = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return groups
      .filter((g) => selectedGroup === 'ALL' || String(g.group_order) === selectedGroup)
      .map((g) => ({
        ...g,
        exercises: g.exercises.filter((ex) => {
          const matchesComplexity =
            selectedComplexity === 'ALL' || ex.complexity === selectedComplexity;
          const matchesSearch =
            !q ||
            ex.popular_name.toLowerCase().includes(q) ||
            ex.primary_muscle.toLowerCase().includes(q) ||
            ex.secondary_muscles.toLowerCase().includes(q) ||
            ex.muscle_group.toLowerCase().includes(q);
          return matchesComplexity && matchesSearch;
        }),
      }))
      .filter((g) => g.exercises.length > 0);
  }, [groups, searchQuery, selectedGroup, selectedComplexity]);

  if (!isOpen) return null;

  const toggleExercise = (exerciseId) => {
    setErrorMsg('');
    setExcludedSet((prev) => {
      const next = new Set(prev);
      if (next.has(exerciseId)) {
        next.delete(exerciseId);
      } else {
        next.add(exerciseId);
      }
      return next;
    });
  };

  const clearExclusions = () => {
    setErrorMsg('');
    setExcludedSet(new Set());
  };

  const handleConfirm = async () => {
    setErrorMsg('');
    try {
      await onConfirmGenerate(Array.from(excludedSet));
    } catch (err) {
      setErrorMsg(err.message || 'Falha ao gerar treino.');
    }
  };

  const excludedCount = excludedSet.size;
  const allowedCount = Math.max(0, totalExercises - excludedCount);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm p-0 sm:p-4">
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-t-3xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[94vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/15 text-orange-400 border border-orange-500/30 mb-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>
                {generationMode === 'SINGLE_DAY'
                  ? `Etapa Pré-Geração — Regenerar Dia ${targetDayNumber}`
                  : 'Etapa Pré-Geração — Montar Treinamento Completo do Zero'}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white">
              Deseja excluir algum exercício antes de montar o treino?
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
              Clique nos exercícios abaixo que você <strong>não quer fazer</strong> (por falta do
              aparelho ou preferência). O Agente LLM Especialista usará apenas os exercícios
              permitidos do banco de dados PostgreSQL.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isGenerating}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors shrink-0"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search & Filters Bar */}
        <div className="px-6 py-3.5 bg-slate-950/70 border-b border-slate-800 grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-5 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Buscar exercício ou músculo (ex: Supino, Agachamento)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500"
            />
          </div>

          <div className="sm:col-span-4 relative">
            <Filter className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-orange-500"
            >
              <option value="ALL">Todos os 9 Grupos Musculares</option>
              {groups.map((g) => (
                <option key={g.group_order} value={String(g.group_order)}>
                  {g.group_order}. {g.muscle_group}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-3">
            <select
              value={selectedComplexity}
              onChange={(e) => setSelectedComplexity(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-orange-500"
            >
              <option value="ALL">Todas Complexidades</option>
              <option value="BAIXA">🟢 Complexidade Baixa</option>
              <option value="MEDIA">🟡 Complexidade Média</option>
              <option value="ALTA">🔴 Complexidade Alta</option>
            </select>
          </div>
        </div>

        {errorMsg && (
          <div className="mx-6 mt-3 p-3 rounded-xl bg-red-500/15 border border-red-500/40 text-red-300 text-sm">
            {errorMsg}
          </div>
        )}

        {/* Exercise List from PostgreSQL */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {isLoadingExercises && groups.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">
              Carregando catálogo de exercícios do banco de dados...
            </div>
          ) : groups.length === 0 ? (
            <div className="text-center py-10 space-y-3">
              <p className="text-slate-400 text-sm">
                Não foi possível carregar o catálogo de exercícios no momento.
              </p>
              {onRetryLoadExercises && (
                <button
                  type="button"
                  onClick={onRetryLoadExercises}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Recarregar Exercícios</span>
                </button>
              )}
            </div>
          ) : filteredGroups.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">
              Nenhum exercício encontrado para o filtro informado.
            </div>
          ) : (
            filteredGroups.map((group) => (
              <div key={group.group_order} className="space-y-2.5">
                <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                  <h3 className="text-sm font-bold text-orange-400 uppercase tracking-wider">
                    {group.group_order}. {group.muscle_group}
                  </h3>
                  <span className="text-xs text-slate-500">
                    {group.exercises.length} exercício(s)
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {group.exercises.map((ex) => {
                    const isExcluded = excludedSet.has(ex.id);
                    const comp = COMPLEXITY_BADGE[ex.complexity] || COMPLEXITY_BADGE.MEDIA;
                    return (
                      <button
                        key={ex.id}
                        type="button"
                        onClick={() => toggleExercise(ex.id)}
                        className={`flex items-start justify-between gap-3 p-3 rounded-xl border text-left transition-all ${
                          isExcluded
                            ? 'bg-rose-950/25 border-rose-500/50 opacity-75'
                            : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span
                              className={`font-semibold text-sm ${
                                isExcluded ? 'line-through text-rose-300' : 'text-white'
                              }`}
                            >
                              {ex.popular_name}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5 truncate">
                            Alvo: {ex.primary_muscle}
                          </p>
                          <div className="flex items-center gap-2 mt-2 flex-wrap">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium border ${comp.classes}`}
                            >
                              {comp.label}
                            </span>
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-900 text-slate-300 border border-slate-800">
                              <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                              {ex.efficiency_score.toFixed(1)}/10
                            </span>
                          </div>
                        </div>

                        <div className="shrink-0 mt-0.5">
                          {isExcluded ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                              <Ban className="w-3.5 h-3.5" />
                              Excluído
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Permitido
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center justify-between sm:justify-start gap-3 text-xs sm:text-sm">
            <span className="text-emerald-400 font-semibold">
              {allowedCount} permitidos
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-rose-400 font-semibold">
              {excludedCount} excluído(s)
            </span>
            {excludedCount > 0 && (
              <button
                type="button"
                onClick={clearExclusions}
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white underline ml-2"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Limpar exclusões
              </button>
            )}
          </div>

          <div className="flex flex-col-reverse sm:flex-row gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={isGenerating}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={isGenerating}
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-bold transition-all shadow-lg shadow-orange-500/25"
            >
              <Sparkles className="w-4 h-4" />
              <span>
                {isGenerating
                  ? 'Agente LLM Montando Treino...'
                  : generationMode === 'SINGLE_DAY'
                  ? `Confirmar e Gerar Novo Treino do Dia ${targetDayNumber}`
                  : 'Confirmar e Gerar Treinamento Completo'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
