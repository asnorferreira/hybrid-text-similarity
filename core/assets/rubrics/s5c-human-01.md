# Instruções para avaliação individual de pares de sentenças

Você avaliará dois textos por vez, chamados Texto A e Texto B. Leia ambos
completamente. Use somente os textos apresentados e estas instruções. Faça a
atividade individualmente, sem IA, ferramentas de similaridade, buscas externas
ou consulta às respostas de outra pessoa. Você pode fazer pausas.

Use seu código de participante. Não escreva nome, e-mail ou documento pessoal.
Na declaração final, informe seu vínculo com o projeto, se já viu os exemplos,
escores ou respostas e se participou da construção dos textos ou modelos.
Responda com sinceridade: exposição ou dúvida deve ser registrada.

## 1. Relação textual

Escolha uma classe somente quando conseguir decidir:

- **Cópia exata:** os dois textos exibidos são idênticos.
- **Cópia editada:** a mesma formulação ainda é reconhecível, com alterações
  locais de grafia, flexão, inserção ou supressão. A proposição central permanece
  recuperável, sem contradição central.
- **Paráfrase:** nova formulação sintática ou lexical preserva a proposição
  central, entidades, números, unidades e relações relevantes. Omissões apenas
  acessórias são possíveis.
- **Sem correspondência detectada:** os textos não sustentam a mesma proposição
  central. Podem ter tema comum, contradição central ou acréscimo dominante
  incompatível. Essa classe não afirma originalidade.

A fronteira entre cópia editada e paráfrase é a continuidade da formulação versus
uma nova formulação da mesma proposição. Se não conseguir resolver a fronteira,
marque **Ambíguo**, explique e deixe a classe vazia. Se o texto estiver corrompido
e incompreensível, marque **Excluído**, explique e deixe a classe vazia.

Exemplos artificiais, usados apenas para explicar a rubrica:

- “O trem saiu às oito.” / “O trem saiu às oito.” → cópia exata.
- “O trem saiu às oito.” / “O trem saíu às oito.” → cópia editada.
- “O trem saiu às oito.” / “Às oito, partiu o trem.” → paráfrase.
- “O trem saiu às oito.” / “O trem não saiu às oito.” → sem correspondência
  detectada, por contradição central.

## 2. Conteúdo compartilhado

Julgue fatos/proposições compartilhados, e não apenas palavras ou assunto.
Escolha uma destas notas, sem interpolar:

| Nota | Significado |
| --- | --- |
| 0 | Nenhuma proposição em comum. |
| 0,25 | Fragmento factual secundário comum, mas núcleo diferente. |
| 0,50 | Proposição central parcial ou contexto factual compartilhado com divergência central. |
| 0,75 | Núcleo compatível preservado, com omissão ou acréscimo relevante. |
| 1 | Equivalência dos fatos nos dois sentidos, sem mudança relevante. |

Contradição não implica automaticamente nota zero: considere os fatos comuns
e registre a contradição. Contradição relevante impede nota 1. A mesma entidade
e evento com negação central podem receber 0,50 se houver conteúdo factual comum
substancial; compartilhar só o assunto não basta. Paráfrase fiel pode receber 1.
Resumo que omite fato importante pode receber 0,75 ou 0,50 conforme o núcleo
preservado. Não calcule nota por porcentagem de palavras conservadas.

Considere entidades, números, datas, unidades, quantificadores, causalidade,
negação e modalidade (por exemplo, “pode” versus “vai”). Se faltarem referências
essenciais para compreender a sentença, marque Ambíguo e deixe a nota vazia.
Texto irrecuperavelmente incompreensível pode ser Excluído com motivo.

Preencha também os quatro eixos:

1. **Tema em comum:** nenhum, algum, forte ou incerto.
2. **Relação entre as proposições:** compatível, contraditória, sem relação ou incerta.
3. **Conteúdo compartilhado:** nenhum, parcial, predominante, equivalente ou incerto.
4. **Contexto:** suficiente ou insuficiente.

Tema forte com proposições sem relação pode ter nota 0. Nota 1 exige proposições
compatíveis, conteúdo equivalente e contexto suficiente.

## 3. Justificativa e trechos

Justifique cada uma das duas decisões brevemente. Diga o que foi mantido,
alterado, omitido ou contradito. Para decisões válidas, copie ao menos um trecho
de cada texto nos campos de evidência; eles precisam existir nos textos exibidos.
Ambiguidade ou exclusão também exige justificativa, com trechos quando possível.
As duas tarefas são separadas: você pode decidir uma e deixar a outra ambígua.

## 4. Salvar e devolver

Use “Salvar rascunho” para baixar um JSON e “Retomar arquivo” para continuar em
outro momento ou computador. O salvamento automático no navegador é apenas uma
comodidade; mantenha o JSON do rascunho como cópia. No fim, complete a declaração
e use “Exportar respostas finais”. Devolva somente o JSON final ao pesquisador.
Não envie o arquivo à outra pessoa e não compare respostas antes da entrega.

## Procedência da rubrica

Aplicação humana s5c-human-01, adaptada das âncoras de conteúdo H1/H2 da rubrica
s5b-rubric-01. As âncoras e classes foram preservadas; instruções de autoavaliação
automatizada foram substituídas pelo procedimento humano. A rubrica não é um
instrumento validado e os julgamentos não comprovam plágio.
