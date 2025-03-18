import pandas as pd
import streamlit as st
import numpy as np

# Optimized Data Loading
@st.cache_data
def load_data(file_path):
    return pd.read_parquet(file_path)

# Client Analysis
def detailed_client_analysis(df, client_id):
    client_df = df[df['codeclient'] == client_id]
    invoice_details = client_df.groupby(['numero', 'month']).agg({'revenue': 'sum', 'quantite': 'sum'}).reset_index()

    freq_months = client_df['month'].nunique()
    monthly_orders = client_df.groupby('month')['numero'].nunique()
    months_present = monthly_orders.reindex(df['month'].unique(), fill_value=0)

    panier_moyen = invoice_details['revenue'].mean()
    monthly_hot_products = (
        client_df.groupby(['month', 'description'])['quantite'].sum()
        .reset_index()
        .sort_values(['month', 'quantite'], ascending=[True, False])
    )

# Keep top 10 per month
    monthly_hot_products = (
        monthly_hot_products.groupby('month').head(10).reset_index(drop=True)
    )
    regulier = 'Régulier' if freq_months >= (df['month'].nunique() // 2) else 'Non Régulier'
    top_products = client_df.groupby('description')['quantite'].sum().nlargest(10)

    avg_commandes_client = invoice_details['quantite'].mean()
    latest_month = df['month'].max()
    ordered_this_month = client_df['month'].max() == latest_month
    orders_this_month = monthly_orders.get(latest_month, 0)

    monthly_order_details = monthly_orders.reset_index().rename(columns={'numero': 'commandes'}).sort_values('month')

    return invoice_details, months_present, panier_moyen, monthly_hot_products, regulier, top_products, avg_commandes_client, monthly_order_details, freq_months

# Overall Analytics
def overall_analytics(df):
    clients_summary = df.groupby('codeclient').agg({
        'revenue': 'sum',
        'numero': 'nunique',
        'month': 'nunique'
    }).rename(columns={'numero': 'total_commandes', 'month': 'mois_commandes'})

    clients_summary['regulier'] = np.where(clients_summary['mois_commandes'] >= (df['month'].nunique() // 2), 'Régulier', 'Non Régulier')
    best_clients = clients_summary.sort_values('revenue', ascending=False).head(10)

    irregular_clients = clients_summary[clients_summary['regulier'] == 'Non Régulier']
    regular_clients = clients_summary[clients_summary['regulier'] == 'Régulier']
    global_avg_panier = df.groupby('numero')['revenue'].sum().mean()

    return clients_summary, best_clients, irregular_clients, regular_clients, global_avg_panier

# Streamlit App
st.set_page_config(page_title="Dashboard Clientèle", layout="wide")
st.title('🚀 **Dashboard Complet d’Analyse des Clients**')

file_path = 'optimized_data.parquet'
df = load_data(file_path)

clients_summary, best_clients, irregular_clients, regular_clients, global_avg_panier = overall_analytics(df)

# Overall Insights
st.header('📌 **Vue d’Ensemble des Clients**')
col1, col2, col3 = st.columns(3)
col1.metric("🧑‍🤝‍🧑 Total Clients", df['codeclient'].nunique())
col2.metric("💰 Panier Moyen Global", f"{global_avg_panier:.2f} dh")
col3.metric("📈 Clients Réguliers", regular_clients.shape[0])

st.subheader('🏆 **Top 10 des Meilleurs Clients (par Revenus)**')
st.dataframe(best_clients.style.format({'revenue': '{:.2f} dh'}))

st.subheader('📅 **Clients Réguliers**')
st.dataframe(regular_clients.reset_index().style.format({'revenue': '{:.2f} dh'}))

st.subheader('⚠️ **Clients Non Réguliers**')
st.dataframe(irregular_clients.reset_index().style.format({'revenue': '{:.2f} dh'}))

# Individual Client Deep-Dive
st.header('🔎 **Analyse Détailée d’un Client**')
selected_client = st.selectbox("Sélectionnez un Client :", df['codeclient'].unique())

(invoice_details, months_present, panier_moyen, monthly_hot_products,
 regulier, top_products, avg_commandes_client, monthly_order_details, freq_months) = detailed_client_analysis(df, selected_client)

st.subheader(f"📌 **Statut du Client {selected_client}** : {regulier}")

col5, col6, col7 = st.columns(3)
col5.metric("💳 Panier Moyen", f"{panier_moyen:.2f} dh")
col6.metric("📦 Quantité Moyenne par Commande", f"{avg_commandes_client:.2f}")
col7.metric("📅 Nombre de Mois Actifs", f"{freq_months} mois")

st.subheader("📊 **Fréquence des Commandes par Mois**")
st.bar_chart(months_present)

st.subheader("📅 **Détails des Commandes par Mois en 2024**")
st.dataframe(monthly_order_details.set_index('month'))

st.subheader("🔥 **Top 10 des Produits par Mois (Produits Chauds)**")
st.dataframe(monthly_hot_products)

st.subheader("🌟 **Top 10 des Produits Préférés du Client**")
st.bar_chart(top_products)

