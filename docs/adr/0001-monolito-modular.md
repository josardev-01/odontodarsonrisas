# ADR 0001: monolito modular como punto de partida

- Estado: propuesto
- Contexto: la aplicacion se desplegara inicialmente en un solo VPS con recursos limitados.
- Opciones: monolito modular; microservicios; aplicacion monolitica sin limites internos.
- Eleccion: FastAPI como monolito modular, con dominios internos bien delimitados.
- Trade-offs: reduce consumo y complejidad operativa; exige disciplina para impedir acoplamiento entre dominios. La separacion futura sigue siendo posible si aparece evidencia operativa.

