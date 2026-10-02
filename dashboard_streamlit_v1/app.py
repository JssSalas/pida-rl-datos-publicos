from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title='PIDA-RL Diabetes México',
    page_icon='🩺',
    layout='wide',
    initial_sidebar_state='expanded',
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR.parent / 'dashboard_data'

DECISION_PATH = DATA_DIR / 'tabla_decision_final_v1.csv'
RISK_PATH = DATA_DIR / 'cobertura_por_riesgo_dashboard_v1.csv'
STABILITY_PATH = DATA_DIR / 'alto_riesgo_por_semilla_dashboard_v1.csv'
CONCLUSIONS_PATH = DATA_DIR / 'conclusiones_dashboard_v1.csv'
CONFIG_PATH = DATA_DIR / 'configuracion_dashboard_v1.json'


@st.cache_data(show_spinner=False)
def load_data():
    required_paths = [DECISION_PATH, RISK_PATH, STABILITY_PATH, CONCLUSIONS_PATH, CONFIG_PATH]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError('No se encontraron estos archivos requeridos:\n' + '\n'.join(missing))

    decision = pd.read_csv(DECISION_PATH)
    risk = pd.read_csv(RISK_PATH)
    stability = pd.read_csv(STABILITY_PATH)
    conclusions = pd.read_csv(CONCLUSIONS_PATH)
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = json.load(file)

    return decision, risk, stability, conclusions, config


def format_boolean(value):
    return 'Sí' if bool(value) else 'No'


def policy_label(policy):
    labels = {
        'aleatoria': 'Aleatoria',
        'reglas_riesgo': 'Reglas de riesgo',
        'reglas_capacidad': 'Reglas con capacidad',
        'dqn_v1': 'DQN',
        'q_learning_v1': 'Q-learning',
        'ppo_v1': 'PPO',
    }
    return labels.get(policy, policy)


def add_labels(frame):
    output = frame.copy()
    if 'politica' in output.columns:
        output['Política'] = output['politica'].map(policy_label)
    return output


def main():
    st.title('Priorización adaptativa de seguimiento en diabetes')
    st.caption('PIDA-RL México | Comparación de políticas en un entorno de simulación')

    st.warning(
        'Resultados de simulación con datos públicos y supuestos explícitos. '
        'Esta aplicación no es un dispositivo médico, no usa datos de pacientes reales '
        'y no debe emplearse para decisiones clínicas individuales.'
    )

    try:
        decision, risk, stability, conclusions, config = load_data()
    except Exception as error:
        st.error(f'No fue posible cargar los datos del dashboard: {error}')
        st.stop()

    selected_policy = config.get('selected_policy', 'No disponible')
    recommendation_status = config.get('recommendation_status', 'No disponible')

    decision = add_labels(decision)
    risk = add_labels(risk)
    stability = add_labels(stability)

    st.sidebar.header('Navegación')
    section = st.sidebar.radio(
        'Selecciona una sección',
        ['Resumen ejecutivo', 'Comparación de políticas', 'Cobertura por riesgo', 'Estabilidad', 'Conclusiones y límites'],
    )

    st.sidebar.divider()
    st.sidebar.subheader('Política de referencia')
    st.sidebar.write(policy_label(selected_policy))
    st.sidebar.caption(recommendation_status.replace('_', ' '))

    if section == 'Resumen ejecutivo':
        st.header('Resumen ejecutivo')
        best = decision.loc[decision['politica'] == selected_policy]
        if best.empty:
            st.info('La política seleccionada no aparece en la tabla de decisión.')
        else:
            best = best.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric('Política de referencia', policy_label(selected_policy))
            col2.metric('Ranking técnico', int(best['ranking_tecnico']))
            col3.metric('Puntaje técnico', f"{best['puntaje_tecnico']:.3f}")
            col4.metric('Cobertura alto riesgo', f"{best['alto']:.2f}%")

            st.subheader('Interpretación')
            st.write(
                'La política de referencia fue seleccionada bajo una regla técnica reproducible: '
                'primer lugar del ranking, respeto promedio de capacidad y cobertura positiva de alto riesgo. '
                'La selección solo aplica al entorno de simulación.'
            )

        st.subheader('Cobertura y capacidad')
        overview_columns = [
            'Política',
            'ranking_tecnico',
            'puntaje_tecnico',
            'alto',
            'excesos_capacidad_medios',
            'respeta_capacidad_en_promedio',
        ]
        overview = decision[[column for column in overview_columns if column in decision.columns]].copy()
        if 'respeta_capacidad_en_promedio' in overview.columns:
            overview['respeta_capacidad_en_promedio'] = overview['respeta_capacidad_en_promedio'].map(format_boolean)
        st.dataframe(overview, use_container_width=True, hide_index=True)

    elif section == 'Comparación de políticas':
        st.header('Comparación de políticas')
        visible_columns = [
            'Política',
            'ranking_tecnico',
            'clasificacion',
            'puntaje_tecnico',
            'recompensa_media',
            'cobertura_alto_riesgo_media',
            'bajo',
            'medio',
            'alto',
            'eventos_adversos_medios',
            'recursos_usados_medios',
            'excesos_capacidad_medios',
            'respeta_capacidad_en_promedio',
        ]
        comparison = decision[[column for column in visible_columns if column in decision.columns]].copy()
        if 'respeta_capacidad_en_promedio' in comparison.columns:
            comparison['respeta_capacidad_en_promedio'] = comparison['respeta_capacidad_en_promedio'].map(format_boolean)
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        chart = px.bar(
            decision.sort_values('ranking_tecnico'),
            x='Política',
            y='puntaje_tecnico',
            color='clasificacion',
            text='puntaje_tecnico',
            title='Puntaje técnico por política',
            labels={'puntaje_tecnico': 'Puntaje técnico', 'clasificacion': 'Tipo de política'},
        )
        chart.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        chart.update_layout(yaxis_range=[0, max(1.0, decision['puntaje_tecnico'].max() * 1.15)])
        st.plotly_chart(chart, use_container_width=True)

        capacity_chart = px.bar(
            decision.sort_values('ranking_tecnico'),
            x='Política',
            y='excesos_capacidad_medios',
            color='respeta_capacidad_en_promedio',
            title='Excesos promedio de capacidad',
            labels={
                'excesos_capacidad_medios': 'Excesos por episodio',
                'respeta_capacidad_en_promedio': 'Respeta capacidad',
            },
        )
        st.plotly_chart(capacity_chart, use_container_width=True)

    elif section == 'Cobertura por riesgo':
        st.header('Cobertura por nivel de riesgo')
        st.write(
            'La cobertura indica el porcentaje de decisiones agregadas por paso en las que el contacto fue aceptado. '
            'En una estrategia de priorización, una cobertura mayor de alto riesgo puede ser coherente con el objetivo, '
            'siempre que los otros niveles no queden sin atención de manera extrema.'
        )

        policy_options = decision.sort_values('ranking_tecnico')['politica'].tolist()
        selected_policies = st.multiselect(
            'Políticas a visualizar',
            options=policy_options,
            default=policy_options,
            format_func=policy_label,
        )
        filtered_risk = risk[risk['politica'].isin(selected_policies)].copy()

        risk_chart = px.bar(
            filtered_risk,
            x='Política',
            y='cobertura_media',
            color='categoria_riesgo',
            barmode='group',
            title='Cobertura media de seguimiento por nivel de riesgo',
            labels={
                'cobertura_media': 'Cobertura media (%)',
                'categoria_riesgo': 'Nivel de riesgo',
            },
            category_orders={'categoria_riesgo': ['bajo', 'medio', 'alto']},
            color_discrete_map={'bajo': '#72B7B2', 'medio': '#F2CF5B', 'alto': '#E45756'},
        )
        st.plotly_chart(risk_chart, use_container_width=True)

        risk_columns = [
            'Política',
            'categoria_riesgo',
            'cobertura_media',
            'cobertura_desviacion',
            'contactos_medios',
            'tasa_eventos_media',
            'costo_medio',
            'excesos_capacidad_medios',
        ]
        st.dataframe(
            filtered_risk[[column for column in risk_columns if column in filtered_risk.columns]],
            use_container_width=True,
            hide_index=True,
        )

    elif section == 'Estabilidad':
        st.header('Estabilidad de cobertura de alto riesgo')
        st.write(
            'La gráfica compara la cobertura de alto riesgo entre las semillas de evaluación. '
            'Diferencias grandes entre semillas sugieren sensibilidad a la inicialización o a la dinámica estocástica del simulador.'
        )

        stability_chart = px.line(
            stability,
            x='semilla',
            y='cobertura_porcentaje',
            color='Política',
            markers=True,
            title='Cobertura de alto riesgo por semilla',
            labels={'semilla': 'Semilla', 'cobertura_porcentaje': 'Cobertura alto riesgo (%)'},
        )
        st.plotly_chart(stability_chart, use_container_width=True)

        stability_columns = [
            'Política',
            'semilla',
            'decisiones',
            'contactos_aceptados',
            'cobertura_porcentaje',
            'eventos_adversos',
            'costo_total',
            'excesos_capacidad',
        ]
        st.dataframe(
            stability[[column for column in stability_columns if column in stability.columns]],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.header('Conclusiones y límites')
        for _, row in conclusions.iterrows():
            label = str(row.get('tipo', 'resultado')).replace('_', ' ').capitalize()
            st.subheader(label)
            st.write(row.get('contenido', ''))

        st.subheader('Limitaciones de la auditoría')
        st.info(
            'La auditoría disponible compara resultados por nivel de riesgo. '
            'No se presentan resultados por sexo ni edad porque las trazas agregadas de evaluación no incluyen '
            'atributos demográficos ni identificadores individuales.'
        )

        st.subheader('Requisitos previos a cualquier uso real')
        st.markdown(
            '- Datos institucionales autorizados y gobernanza de datos.\n'
            '- Validación clínica y evaluación prospectiva.\n'
            '- Auditoría de desempeño y equidad con subgrupos demográficos observables.\n'
            '- Revisión ética, trazabilidad, monitoreo y supervisión humana.'
        )


if __name__ == '__main__':
    main()
