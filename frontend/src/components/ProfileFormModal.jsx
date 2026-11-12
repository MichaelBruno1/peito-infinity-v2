import React, { useEffect, useState } from 'react';
import { X, User, Scale, Ruler, Flame, Dumbbell, Zap, Clock, Calendar } from 'lucide-react';

const FITNESS_LEVELS = [
  { value: 'INICIANTE', label: 'Iniciante', desc: 'Iniciando ou retornando à academia' },
  { value: 'INTERMEDIARIO', label: 'Intermediário', desc: 'Treina regularmente há mais de 6 meses' },
  { value: 'AVANCADO', label: 'Avançado', desc: 'Alta consciência corporal e domínio técnico' },
];

const GOALS = [
  {
    value: 'EMAGRECIMENTO',
    label: 'Emagrecimento',
    desc: 'Alto gasto calórico, densidade metabólica e cardio estratégico',
    icon: Flame,
  },
  {
    value: 'HIPERTROFIA',
    label: 'Hipertrofia',
    desc: 'Ganho de massa muscular com foco em eficiência e tensão mecânica',
    icon: Dumbbell,
  },
  {
    value: 'FORCA',
    label: 'Treino de Força',
    desc: 'Progressão de carga máxima em multiarticulares e recuperação neural',
    icon: Zap,
  },
];

export default function ProfileFormModal({ isOpen, onClose, onSubmit, initialData, isSubmitting }) {
  const [form, setForm] = useState({
    name: '',
    weight_kg: 75,
    height_cm: 175,
    fitness_level: 'INTERMEDIARIO',
    goal: 'HIPERTROFIA',
    available_time_minutes: 60,
    days_per_week: 4,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialData) {
      setForm({
        name: initialData.name || '',
        weight_kg: initialData.weight_kg ?? 75,
        height_cm: initialData.height_cm ?? 175,
        fitness_level: initialData.fitness_level || 'INTERMEDIARIO',
        goal: initialData.goal || 'HIPERTROFIA',
        available_time_minutes: initialData.available_time_minutes ?? 60,
        days_per_week: initialData.days_per_week ?? 4,
      });
    } else {
      setForm({
        name: '',
        weight_kg: 75,
        height_cm: 175,
        fitness_level: 'INTERMEDIARIO',
        goal: 'HIPERTROFIA',
        available_time_minutes: 60,
        days_per_week: 4,
      });
    }
    setError('');
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.name.trim() || form.name.trim().length < 2) {
      setError('Informe um nome válido com pelo menos 2 caracteres.');
      return;
    }
    try {
      await onSubmit({
        name: form.name.trim(),
        weight_kg: Number(form.weight_kg),
        height_cm: Number(form.height_cm),
        fitness_level: form.fitness_level,
        goal: form.goal,
        available_time_minutes: Number(form.available_time_minutes),
        days_per_week: Number(form.days_per_week),
      });
    } catch (err) {
      setError(err.message || 'Erro ao salvar perfil.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/75 backdrop-blur-sm p-0 sm:p-4 overflow-y-auto">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-t-3xl sm:rounded-2xl shadow-2xl overflow-hidden max-h-[94vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div>
            <h2 className="text-xl font-bold text-white">
              {initialData ? 'Editar Perfil de Treino' : 'Novo Perfil de Usuário'}
            </h2>
            <p className="text-xs text-slate-400">
              Acesso direto na rede doméstica — sem necessidade de senha ou login
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/15 border border-red-500/40 text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Nome */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Nome do Praticante
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                minLength={2}
                maxLength={80}
                placeholder="Ex: Rodrigo, Ana, Marcos..."
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
            </div>
          </div>

          {/* Peso e Altura */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Peso Corporal (kg)
              </label>
              <div className="relative">
                <Scale className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="number"
                  step="0.1"
                  min={25}
                  max={300}
                  required
                  value={form.weight_kg}
                  onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-orange-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Altura (cm)
              </label>
              <div className="relative">
                <Ruler className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="number"
                  step="1"
                  min={100}
                  max={250}
                  required
                  value={form.height_cm}
                  onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-orange-500"
                />
              </div>
            </div>
          </div>

          {/* Nível de Condicionamento Físico */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Nível de Condicionamento Físico
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {FITNESS_LEVELS.map((lvl) => {
                const active = form.fitness_level === lvl.value;
                return (
                  <button
                    key={lvl.value}
                    type="button"
                    onClick={() => setForm({ ...form, fitness_level: lvl.value })}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      active
                        ? 'bg-orange-500/15 border-orange-500 text-white shadow-sm'
                        : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-semibold text-sm">{lvl.label}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{lvl.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Objetivo */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Objetivo Principal
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {GOALS.map((g) => {
                const Icon = g.icon;
                const active = form.goal === g.value;
                return (
                  <button
                    key={g.value}
                    type="button"
                    onClick={() => setForm({ ...form, goal: g.value })}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      active
                        ? 'bg-orange-500/15 border-orange-500 text-white shadow-sm'
                        : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 font-semibold text-sm">
                      <Icon className={`w-4 h-4 ${active ? 'text-orange-400' : 'text-slate-400'}`} />
                      <span>{g.label}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1 leading-relaxed">{g.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tempo Disponível por Dia e Dias na Semana */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Tempo Disponível por Dia (minutos)
              </label>
              <div className="relative">
                <Clock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="number"
                  min={20}
                  max={240}
                  step={5}
                  required
                  value={form.available_time_minutes}
                  onChange={(e) =>
                    setForm({ ...form, available_time_minutes: e.target.value })
                  }
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-orange-500"
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Ex: 45, 60, 75 ou 90 minutos por sessão
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Dias de Treino na Semana
              </label>
              <div className="grid grid-cols-7 gap-1.5">
                {[1, 2, 3, 4, 5, 6, 7].map((dayNum) => {
                  const selected = Number(form.days_per_week) === dayNum;
                  return (
                    <button
                      key={dayNum}
                      type="button"
                      onClick={() => setForm({ ...form, days_per_week: dayNum })}
                      className={`py-3 rounded-xl font-bold text-sm border transition-all ${
                        selected
                          ? 'bg-orange-500 border-orange-500 text-white shadow'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                      }`}
                    >
                      {dayNum}x
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                <span>{form.days_per_week} dia(s) de treino por semana</span>
              </p>
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-semibold text-sm transition-colors shadow-lg shadow-orange-500/20"
            >
              {isSubmitting
                ? 'Salvando...'
                : initialData
                ? 'Salvar Alterações do Perfil'
                : 'Criar Perfil'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
