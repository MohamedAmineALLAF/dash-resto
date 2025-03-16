import pandas as pd
import streamlit as st
import numpy as np

# Optimized Data Loading
def load_data(file_path):
    df = pd.read_parquet(file_path)
    return df

# Client Analysis
def detailed_client_analysis(df, client_id):
    client_df = df[df['codeclient'] == client_id]
    invoice_details = client_df.groupby(['numero', 'month']).agg({'revenue':'sum', 'quantite':'sum'}).reset_index()

    freq_months = client_df['month'].nunique()
    monthly_orders = client_df.groupby('month')['numero'].nunique()
    months_present = monthly_orders.reindex(df['month'].unique(), fill_value=0)

    panier_moyen = invoice_details['revenue'].mean()

    monthly_hot_products = client_df.groupby(['month', 'description']).quantite.sum().groupby(level=0, group_keys=False).nlargest(3).reset_index()

    regulier = 'Régulier' if freq_months >= (df['month'].nunique() // 2) else 'Non Régulier'

    top_products = client_df.groupby('description')['quantite'].sum().nlargest(10)

    avg_commandes_client = invoice_details['quantite'].mean()
    ordered_this_month = client_df['month'].max() == df['month'].max()
    orders_this_month = monthly_orders.get(df['month'].max(), 0)

    return invoice_details, months_present, panier_moyen, monthly_hot_products, regulier, top_products, avg_commandes_client, ordered_this_month, orders_this_month

# Overall Analytics
def overall_analytics(df):
    clients_summary = df.groupby('codeclient').agg({
        'revenue':'sum', 'numero':'nunique', 'month':'nunique', 'quantite':'mean'
    }).rename(columns={'numero':'total_commandes', 'month':'mois_commandes', 'quantite':'moyen_commandes_par_client'})

    clients_summary['regulier'] = np.where(clients_summary['mois_commandes'] >= (df['month'].nunique() // 2), 'Régulier', 'Non Régulier')

    best_clients = clients_summary.sort_values('revenue', ascending=False).head(10)

    irregular_clients = clients_summary[clients_summary['regulier'] == 'Non Régulier']
    regular_clients = clients_summary[clients_summary['regulier'] == 'Régulier']

    global_avg_panier = df.groupby('numero')['revenue'].sum().mean()
    global_avg_commandes = clients_summary['moyen_commandes_par_client'].mean()

    return clients_summary, best_clients, irregular_clients, regular_clients, global_avg_panier, global_avg_commandes

# Streamlit App
st.title('🚀 Dashboard Complet d’Analyse des Clients')

file_path = 'optimized_data.parquet'
df = load_data(file_path)

clients_summary, best_clients, irregular_clients, regular_clients, global_avg_panier, global_avg_commandes = overall_analytics(df)

# Overall Insights
st.header('📌 Insights Globaux')
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Clients", df['codeclient'].nunique())
col2.metric("Panier Moyen Global", f"{global_avg_panier:.2f}")
col3.metric("Moyen Global des Commandes", f"{global_avg_commandes:.2f}")
col4.metric("Clients Réguliers", regular_clients.shape[0])

st.subheader('🏆 Top 10 Meilleurs Clients (par Revenus)')
st.dataframe(best_clients)

st.subheader('Clients Réguliers 📅')
st.dataframe(regular_clients.reset_index())

st.subheader('Clients Non Réguliers ⚠️')
st.dataframe(irregular_clients.reset_index())

# Individual Client Deep-Dive
st.header('🔍 Analyse Détailée par Client')
selected_client = st.selectbox("Sélectionnez un Client", df['codeclient'].unique())

invoice_details, months_present, panier_moyen, monthly_hot_products, regulier, top_products, avg_commandes_client, ordered_this_month, orders_this_month = detailed_client_analysis(df, selected_client)

st.subheader(f"Statut du Client {selected_client}: {regulier}")

col5, col6, col7 = st.columns(3)
col5.metric("Panier Moyen", f"{panier_moyen:.2f}")
col6.metric("Commande Moyenne", f"{avg_commandes_client:.2f}")
col7.metric("Commandes Ce Mois", orders_this_month if ordered_this_month else "Aucune")

st.subheader("📅 Fréquence des commandes par mois")
st.bar_chart(months_present)

st.subheader("🔥 Produits Chauds par Mois")
st.dataframe(monthly_hot_products)

st.subheader("🌟 Top 10 Produits du Client")
st.bar_chart(top_products)
