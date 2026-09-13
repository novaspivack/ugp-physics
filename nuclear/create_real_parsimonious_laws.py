#!/usr/bin/env python3
"""
Create the REAL most parsimonious laws based on systematic analysis
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import pickle

def calculate_gte_features(Z, N, A):
    """Calculate GTE features for a single nucleus - matching distilled model expectations"""
    # Calculate GTE triples
    a_eff = Z * (Z - 1) / A
    b_eff = N * (N - 1) / A
    c_eff = (N - Z) * (N - Z - 1) / A
    g_eff = A**(2/3)
    
    # Calculate the exact 10 features expected by distilled models
    features = []
    feature_names = []
    
    # 1. log_b_eff
    features.append(np.log(b_eff + 1))
    feature_names.append('log_b_eff')
    
    # 2. log_g_eff
    features.append(np.log(g_eff + 1))
    feature_names.append('log_g_eff')
    
    # 3. log_a_eff
    features.append(np.log(a_eff + 1))
    feature_names.append('log_a_eff')
    
    # 4. asymmetry_sq
    asymmetry = (N - Z) / A
    features.append(asymmetry**2)
    feature_names.append('asymmetry_sq')
    
    # 5. exp_neg_a_eff
    features.append(np.exp(-a_eff/100))
    feature_names.append('exp_neg_a_eff')
    
    # 6. exp_neg_b_eff
    features.append(np.exp(-b_eff/100))
    feature_names.append('exp_neg_b_eff')
    
    # 7. log_b_x_coulomb
    coulomb = Z**2 / A**(4/3)
    features.append(np.log(b_eff + 1) * coulomb)
    feature_names.append('log_b_x_coulomb')
    
    # 8. log_a_x_asymmetry
    features.append(np.log(a_eff + 1) * asymmetry)
    feature_names.append('log_a_x_asymmetry')
    
    # 9. a_eff
    features.append(a_eff)
    feature_names.append('a_eff')
    
    # 10. coulomb
    features.append(coulomb)
    feature_names.append('coulomb')
    
    return np.array(features), feature_names

def create_real_parsimonious_laws():
    """Create the REAL most parsimonious laws"""
    
    print("🔍 CREATING REAL MOST PARSIMONIOUS LAWS")
    print("="*80)
    
    # Load dataset
    df = pd.read_csv('unified_gte_training_dataset_with_stability.csv')
    print(f"Loaded dataset: {len(df)} nuclei")
    
    # Calculate features for all nuclei
    features_list = []
    for _, row in df.iterrows():
        Z, N, A = int(row['Z']), int(row['N']), int(row['A'])
        features, feature_names = calculate_gte_features(Z, N, A)
        features_list.append(features)
    
    X = np.array(features_list)
    y_be = df['BE_per_A'].values
    y_stability = df['Is_Stable'].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"Features shape: {X_scaled.shape}")
    print(f"Feature names: {feature_names}")
    
    # Create 5-term binding energy law
    print(f"\n{'='*80}")
    print("CREATING 5-TERM BINDING ENERGY LAW")
    print(f"{'='*80}")
    
    # Use first 5 features: ['log_b_eff', 'log_g_eff', 'log_a_eff', 'asymmetry_sq', 'exp_neg_a_eff']
    X_be = X_scaled[:, :5]
    be_feature_names = feature_names[:5]
    
    # Train Ridge regression
    ridge_be = Ridge(alpha=1.0)
    ridge_be.fit(X_be, y_be)
    
    # Evaluate performance
    y_pred_be = ridge_be.predict(X_be)
    be_mae = mean_absolute_error(y_be, y_pred_be)
    be_r2 = r2_score(y_be, y_pred_be)
    
    print(f"5-term binding energy law performance:")
    print(f"  MAE: {be_mae:.6f} MeV")
    print(f"  R²: {be_r2:.6f}")
    print(f"  Features: {be_feature_names}")
    print(f"  Coefficients: {ridge_be.coef_}")
    print(f"  Intercept: {ridge_be.intercept_}")
    
    # Create 1-term stability law
    print(f"\n{'='*80}")
    print("CREATING 1-TERM STABILITY LAW")
    print(f"{'='*80}")
    
    # Use first 1 feature: ['log_b_eff']
    X_stability = X_scaled[:, :1]
    stability_feature_names = feature_names[:1]
    
    # Train Ridge regression
    ridge_stability = Ridge(alpha=1.0)
    ridge_stability.fit(X_stability, y_stability)
    
    # Evaluate performance
    y_pred_stability = ridge_stability.predict(X_stability)
    stability_mae = mean_absolute_error(y_stability, y_pred_stability)
    stability_r2 = r2_score(y_stability, y_pred_stability)
    stability_accuracy = np.mean((y_pred_stability > 0.5) == y_stability)
    
    print(f"1-term stability law performance:")
    print(f"  MAE: {stability_mae:.6f}")
    print(f"  R²: {stability_r2:.6f}")
    print(f"  Accuracy: {stability_accuracy:.4f} ({stability_accuracy*100:.2f}%)")
    print(f"  Features: {stability_feature_names}")
    print(f"  Coefficients: {ridge_stability.coef_}")
    print(f"  Intercept: {ridge_stability.intercept_}")
    
    # Save the models
    print(f"\n{'='*80}")
    print("SAVING REAL PARSIMONIOUS LAWS")
    print(f"{'='*80}")
    
    # Save binding energy law
    binding_law = {
        'model': ridge_be,
        'scaler': scaler,
        'feature_names': be_feature_names,
        'mae': be_mae,
        'r2': be_r2,
        'n_terms': 5
    }
    
    with open('canonical_models/real_parsimonious_binding_law.pkl', 'wb') as f:
        pickle.dump(binding_law, f)
    
    # Save stability law
    stability_law = {
        'model': ridge_stability,
        'scaler': scaler,
        'feature_names': stability_feature_names,
        'mae': stability_mae,
        'r2': stability_r2,
        'accuracy': stability_accuracy,
        'n_terms': 1
    }
    
    with open('canonical_models/real_parsimonious_stability_law.pkl', 'wb') as f:
        pickle.dump(stability_law, f)
    
    print("Saved real parsimonious laws to:")
    print("  - canonical_models/real_parsimonious_binding_law.pkl")
    print("  - canonical_models/real_parsimonious_stability_law.pkl")
    
    # Create mathematical expressions
    print(f"\n{'='*80}")
    print("MATHEMATICAL EXPRESSIONS")
    print(f"{'='*80}")
    
    print("REAL 5-Term Binding Energy Law:")
    print(f"BE/A = {ridge_be.intercept_:.6f}")
    for i, (coef, feature) in enumerate(zip(ridge_be.coef_, be_feature_names)):
        sign = "+" if coef >= 0 else "-"
        print(f"     {sign} {abs(coef):.6f} * {feature}")
    
    print(f"\nREAL 1-Term Stability Law:")
    print(f"P(Stable) = σ({ridge_stability.intercept_:.6f}")
    for i, (coef, feature) in enumerate(zip(ridge_stability.coef_, stability_feature_names)):
        sign = "+" if coef >= 0 else "-"
        print(f"           {sign} {abs(coef):.6f} * {feature}")
    print("           )")
    
    return binding_law, stability_law

def test_real_laws():
    """Test the real laws on specific nuclei"""
    
    print(f"\n{'='*80}")
    print("TESTING REAL LAWS ON SPECIFIC NUCLEI")
    print(f"{'='*80}")
    
    # Load the real laws
    with open('canonical_models/real_parsimonious_binding_law.pkl', 'rb') as f:
        binding_law = pickle.load(f)
    
    with open('canonical_models/real_parsimonious_stability_law.pkl', 'rb') as f:
        stability_law = pickle.load(f)
    
    # Test nuclei
    test_nuclei = [
        (6, 6, 12),   # Carbon-12
        (8, 8, 16),   # Oxygen-16
        (26, 30, 56), # Iron-56
        (82, 126, 208), # Lead-208
        (92, 146, 238)  # Uranium-238
    ]
    
    for Z, N, A in test_nuclei:
        print(f"\n{Z:2d}-{A:3d} (Z={Z}, N={N}):")
        
        # Calculate features
        features, _ = calculate_gte_features(Z, N, A)
        
        # Binding energy prediction
        X_scaled = binding_law['scaler'].transform(features.reshape(1, -1))
        X_be = X_scaled[:, :5]  # First 5 features
        be_pred = binding_law['model'].predict(X_be)[0]
        
        # Stability prediction
        X_stability = X_scaled[:, :1]  # First 1 feature
        stability_pred = stability_law['model'].predict(X_stability)[0]
        stability_prob = 1 / (1 + np.exp(-stability_pred))
        
        print(f"  Binding Energy: {be_pred:.6f} MeV/nucleon")
        print(f"  Stability: {stability_prob:.6f} ({stability_prob*100:.2f}%)")

def main():
    """Main function"""
    
    print("🔍 CREATING REAL MOST PARSIMONIOUS LAWS")
    print("="*80)
    print("Based on systematic analysis of parsimony vs performance tradeoff")
    
    # Create the real laws
    binding_law, stability_law = create_real_parsimonious_laws()
    
    # Test the laws
    test_real_laws()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("✅ Created REAL most parsimonious laws:")
    print(f"  - 5-term binding energy law: {binding_law['mae']:.6f} MeV MAE, {binding_law['r2']:.6f} R²")
    print(f"  - 1-term stability law: {stability_law['mae']:.6f} MAE, {stability_law['r2']:.6f} R², {stability_law['accuracy']:.4f} accuracy")
    print("✅ Saved models to canonical_models/")
    print("✅ Ready for integration into the app")

if __name__ == "__main__":
    main()
