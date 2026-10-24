export function format(value: number, places = 2) {
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: places, maximumFractionDigits: places,
    roundingMode: 'halfExpand' }).format(value);
}
export const labels: Record<string, string> = { copia_exata: 'Cópia exata', copia_editada: 'Cópia editada',
  parafrase: 'Paráfrase', sem_correspondencia_detectada: 'Sem correspondência detectada', sem_predominancia: 'Sem predominância' };
export const reasons: Record<string, string> = { igualdade_da_representacao_textual: 'Igualdade após limpeza, sensível a maiúsculas',
  semelhanca_estrutural: 'Levenshtein no limiar configurado ou acima; precede a regra semântica',
  escores_baixos_sem_evidencia_estrutural: 'Máximo dos escores até o corte configurado, sem evidência estrutural suficiente',
  similaridade_semantica_operacional: 'Cosseno operacional acima do limiar configurado, após as regras anteriores',
  evidencia_insuficiente_pelas_regras: 'Evidência insuficiente pelas regras provisórias' };
