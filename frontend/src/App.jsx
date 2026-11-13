import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Dumbbell, Wifi, CheckCircle2 } from 'lucide-react';
import { api } from './services/api.js';
import ProfileSelectorView from './components/ProfileSelectorView.jsx';
import WorkoutDashboardView from './components/WorkoutDashboardView.jsx';
import ProfileFormModal from './components/ProfileFormModal.jsx';
import ExerciseExclusionModal from './components/ExerciseExclusionModal.jsx';

const EMPTY_EXCLUDED_IDS = [];

export default function App() {
  const queryClient = useQueryClient();
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [profileModalState, setProfileModalState] = useState({
    isOpen: false,
    editingProfile: null,
  });
  const [exclusionModalState, setExclusionModalState] = useState({
    isOpen: false,
    mode: 'FULL', // 'FULL' | 'SINGLE_DAY'
    dayNumber: null,
  });
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((curr) => (curr === msg ? null : curr));
    }, 4000);
  };

  // Queries
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  });

  const profilesQuery = useQuery({
    queryKey: ['profiles'],
    queryFn: api.getProfiles,
  });

  const exercisesQuery = useQuery({
    queryKey: ['exercises'],
    queryFn: api.getExercises,
  });

  const activeProfileQuery = useQuery({
    queryKey: ['profile', selectedProfileId],
    queryFn: () => api.getProfile(selectedProfileId),
    enabled: Boolean(selectedProfileId),
  });

  // Mutations
  const createProfileMutation = useMutation({
    mutationFn: api.createProfile,
    onSuccess: (created) => {
      queryClient.setQueryData(['profile', created.id], created);
      queryClient.setQueryData(['profiles'], (old) =>
        Array.isArray(old) ? [created, ...old.filter((p) => p.id !== created.id)] : [created]
      );
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      if (!exercisesQuery.data?.groups?.length) {
        exercisesQuery.refetch();
      }
      setProfileModalState({ isOpen: false, editingProfile: null });
      setSelectedProfileId(created.id);
      showToast(`Perfil "${created.name}" criado com sucesso!`);
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: ({ id, payload }) => api.updateProfile(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['profile', updated.id], updated);
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      queryClient.invalidateQueries({ queryKey: ['profile', updated.id] });
      setProfileModalState({ isOpen: false, editingProfile: null });
      showToast(`Perfil "${updated.name}" atualizado!`);
    },
  });

  const deleteProfileMutation = useMutation({
    mutationFn: (id) => api.deleteProfile(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      if (selectedProfileId === deletedId) {
        setSelectedProfileId(null);
      }
      showToast('Perfil removido com sucesso.');
    },
  });

  const generateFullWorkoutMutation = useMutation({
    mutationFn: ({ profileId, excludedIds }) =>
      api.generateFullWorkout(profileId, excludedIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      queryClient.invalidateQueries({ queryKey: ['profile', selectedProfileId] });
      setExclusionModalState({ isOpen: false, mode: 'FULL', dayNumber: null });
      showToast('Treinamento completo gerado com sucesso pelo Agente Especialista!');
    },
  });

  const regenerateDayMutation = useMutation({
    mutationFn: ({ profileId, dayNumber, excludedIds }) =>
      api.regenerateWorkoutDay(profileId, dayNumber, excludedIds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      queryClient.invalidateQueries({ queryKey: ['profile', selectedProfileId] });
      setExclusionModalState({ isOpen: false, mode: 'FULL', dayNumber: null });
      showToast(`Novo treino do Dia ${variables.dayNumber} gerado com sucesso!`);
    },
  });

  const handleSaveProfile = async (payload) => {
    if (profileModalState.editingProfile) {
      await updateProfileMutation.mutateAsync({
        id: profileModalState.editingProfile.id,
        payload,
      });
    } else {
      await createProfileMutation.mutateAsync(payload);
    }
  };

  const handleDeleteProfile = async (profile) => {
    if (window.confirm(`Deseja realmente remover o perfil "${profile.name}"?`)) {
      await deleteProfileMutation.mutateAsync(profile.id);
    }
  };

  const handleConfirmGenerate = async (excludedExerciseIds) => {
    if (!selectedProfileId) return;
    if (exclusionModalState.mode === 'SINGLE_DAY' && exclusionModalState.dayNumber) {
      await regenerateDayMutation.mutateAsync({
        profileId: selectedProfileId,
        dayNumber: exclusionModalState.dayNumber,
        excludedIds: excludedExerciseIds,
      });
    } else {
      await generateFullWorkoutMutation.mutateAsync({
        profileId: selectedProfileId,
        excludedIds: excludedExerciseIds,
      });
    }
  };

  const currentProfile = activeProfileQuery.data;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Global Responsive Header */}
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => setSelectedProfileId(null)}
            className="flex items-center gap-3 text-left group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-lg shadow-orange-500/20">
              <Dumbbell className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-extrabold tracking-tight text-white group-hover:text-orange-400 transition-colors">
                Peito <span className="text-orange-500">Infinity</span>
              </span>
              <span className="block text-[11px] text-slate-400 leading-none">
                Treinador Inteligente com Agente LLM
              </span>
            </div>
          </button>
        </div>
      </header>

      {/* Toast Feedback */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-3 rounded-2xl bg-emerald-600 text-white text-sm font-semibold shadow-2xl border border-emerald-400/30 animate-bounce">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1">
        {!selectedProfileId ? (
          <ProfileSelectorView
            profiles={profilesQuery.data || []}
            isLoading={profilesQuery.isLoading}
            isError={profilesQuery.isError}
            onRetry={() => profilesQuery.refetch()}
            exercisesCount={healthQuery.data?.exercises_count || exercisesQuery.data?.total || 94}
            onSelectProfile={(id) => {
              if (!exercisesQuery.data?.groups?.length) {
                exercisesQuery.refetch();
              }
              setSelectedProfileId(id);
            }}
            onOpenCreateProfile={() =>
              setProfileModalState({ isOpen: true, editingProfile: null })
            }
            onOpenEditProfile={(prof) =>
              setProfileModalState({ isOpen: true, editingProfile: prof })
            }
            onDeleteProfile={handleDeleteProfile}
          />
        ) : activeProfileQuery.isLoading || !currentProfile ? (
          <div className="max-w-4xl mx-auto px-4 py-20 text-center text-slate-400">
            Carregando dados do perfil...
          </div>
        ) : (
          <WorkoutDashboardView
            profile={currentProfile}
            onBackToProfiles={() => setSelectedProfileId(null)}
            onOpenEditProfile={(prof) =>
              setProfileModalState({ isOpen: true, editingProfile: prof })
            }
            onRequestGenerateFull={() => {
              if (!exercisesQuery.data?.groups?.length || exercisesQuery.isError) {
                exercisesQuery.refetch();
              }
              setExclusionModalState({ isOpen: true, mode: 'FULL', dayNumber: null });
            }}
            onRequestRegenerateDay={(dayNum) => {
              if (!exercisesQuery.data?.groups?.length || exercisesQuery.isError) {
                exercisesQuery.refetch();
              }
              setExclusionModalState({
                isOpen: true,
                mode: 'SINGLE_DAY',
                dayNumber: dayNum,
              });
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-5 px-4 text-center text-xs text-slate-500">
        Peito Infinity • Executando em Docker + PostgreSQL + Python FastAPI + React • Rede Local
      </footer>

      {/* Create / Edit Profile Modal */}
      <ProfileFormModal
        isOpen={profileModalState.isOpen}
        onClose={() => setProfileModalState({ isOpen: false, editingProfile: null })}
        onSubmit={handleSaveProfile}
        initialData={profileModalState.editingProfile}
        isSubmitting={createProfileMutation.isPending || updateProfileMutation.isPending}
      />

      {/* Pre-Generation Exercise Exclusion Modal */}
      <ExerciseExclusionModal
        isOpen={exclusionModalState.isOpen}
        onClose={() =>
          setExclusionModalState({ isOpen: false, mode: 'FULL', dayNumber: null })
        }
        onConfirmGenerate={handleConfirmGenerate}
        exerciseCatalog={exercisesQuery.data}
        isLoadingExercises={exercisesQuery.isLoading || exercisesQuery.isFetching}
        onRetryLoadExercises={() => exercisesQuery.refetch()}
        profileId={selectedProfileId}
        initialExcludedIds={currentProfile?.excluded_exercise_ids || EMPTY_EXCLUDED_IDS}
        generationMode={exclusionModalState.mode}
        targetDayNumber={exclusionModalState.dayNumber}
        isGenerating={
          generateFullWorkoutMutation.isPending || regenerateDayMutation.isPending
        }
      />
    </div>
  );
}
