import React from 'react';
import {
  Plus,
  Dumbbell,
  Clock,
  Calendar,
  Flame,
  Zap,
  ChevronRight,
  Trash2,
  Edit3,
  Database,
  RefreshCw,
} from 'lucide-react';

const GOAL_INFO = {
  EMAGRECIMENTO: {
    label: 'Emagrecimento',
    badgeClass: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    icon: Flame,
  },
  HIPERTROFIA: {
    label: 'Hipertrofia',
    badgeClass: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
    icon: Dumbbell,
  },
  FORCA: {
    label: 'Treino de Força',
    badgeClass: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    icon: Zap,
  },
};

const LEVEL_LABELS = {
  INICIANTE: 'Iniciante',
  INTERMEDIARIO: 'Intermediário',
  AVANCADO: 'Avançado',
};

const GENDER_LABELS = {
  MASCULINO: 'Masculino',
  FEMININO: 'Feminino',
};

export default function ProfileSelectorView({
  profiles,
  isLoading = false,
  isError = false,
  onRetry,
  exercisesCount,
  onSelectProfile,
  onOpenCreateProfile,
  onOpenEditProfile,
  onDeleteProfile,
}) {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-10">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900 to-orange-950/40 border border-slate-800 p-6 sm:p-10 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Quem vai treinar hoje no <span className="text-orange-500">Peito Infinity</span>?
            </h1>
          </div>

          <button
            type="button"
            onClick={onOpenCreateProfile}
            className="inline-flex items-center justify-center gap-2.5 px-6 py-4 rounded-2xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-sm sm:text-base transition-all shadow-xl shadow-orange-500/25 shrink-0"
          >
            <Plus className="w-5 h-5" />
            <span>Criar Novo Perfil</span>
          </button>
        </div>
      </div>

      {/* Profiles Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg sm:text-xl font-bold text-white">
            Perfis de Usuário ({profiles.length})
          </h2>
        </div>

        {isLoading && profiles.length === 0 ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-10 sm:p-14 text-center text-slate-400 text-sm">
            Carregando perfis de usuário...
          </div>
        ) : isError && profiles.length === 0 ? (
          <div className="rounded-3xl border border-rose-500/30 bg-slate-900/50 p-10 sm:p-14 text-center space-y-4">
            <p className="text-sm text-rose-300">
              Erro ao carregar os perfis de usuário da API.
            </p>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Tentar Novamente</span>
              </button>
            )}
          </div>
        ) : profiles.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/50 p-10 sm:p-14 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-orange-500/15 border border-orange-500/30 flex items-center justify-center mx-auto text-orange-400">
              <Dumbbell className="w-8 h-8" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h3 className="text-lg font-bold text-white">Nenhum perfil criado ainda</h3>
              <p className="text-sm text-slate-400">
                Crie o primeiro perfil informando nome, peso, altura, condicionamento, objetivo,
                tempo disponível em minutos e dias na semana.
              </p>
            </div>
            <button
              type="button"
              onClick={onOpenCreateProfile}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Criar Primeiro Perfil</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {profiles.map((profile) => {
              const goalMeta = GOAL_INFO[profile.goal] || GOAL_INFO.HIPERTROFIA;
              const GoalIcon = goalMeta.icon;
              const initials = profile.name
                .split(' ')
                .map((n) => n[0])
                .join('')
                .slice(0, 2)
                .toUpperCase();

              return (
                <div
                  key={profile.id}
                  className="group relative rounded-2xl bg-slate-900 border border-slate-800 hover:border-orange-500/60 transition-all p-5 flex flex-col justify-between shadow-lg"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3.5">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-extrabold text-lg flex items-center justify-center shadow-md shrink-0">
                          {initials}
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-white group-hover:text-orange-400 transition-colors">
                            {profile.name}
                          </h3>
                          <p className="text-xs text-slate-400">
                            {profile.weight_kg} kg • {profile.height_cm} cm (IMC {profile.bmi})
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenEditProfile(profile);
                          }}
                          title="Editar Perfil"
                          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteProfile(profile);
                          }}
                          title="Excluir Perfil"
                          className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 mt-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${goalMeta.badgeClass}`}
                      >
                        <GoalIcon className="w-3.5 h-3.5" />
                        {goalMeta.label}
                      </span>
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 text-slate-300">
                        {GENDER_LABELS[profile.gender] || 'Masculino'}
                      </span>
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 text-slate-300">
                        {LEVEL_LABELS[profile.fitness_level] || profile.fitness_level}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2.5 mt-4 pt-4 border-t border-slate-800/80 text-xs text-slate-300">
                      <div className="flex items-center gap-2 bg-slate-950/70 px-3 py-2 rounded-xl border border-slate-800/70">
                        <Clock className="w-4 h-4 text-orange-400 shrink-0" />
                        <span>{profile.available_time_minutes} min / dia</span>
                      </div>
                      <div className="flex items-center gap-2 bg-slate-950/70 px-3 py-2 rounded-xl border border-slate-800/70">
                        <Calendar className="w-4 h-4 text-orange-400 shrink-0" />
                        <span>{profile.days_per_week} dias / sem</span>
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => onSelectProfile(profile.id)}
                    className="mt-5 w-full inline-flex items-center justify-between px-4 py-3 rounded-xl bg-slate-800/90 group-hover:bg-orange-500 text-white font-semibold text-sm transition-all"
                  >
                    <span>
                      {profile.has_active_workout ? 'Abrir Meu Treino' : 'Configurar e Gerar Treino'}
                    </span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
