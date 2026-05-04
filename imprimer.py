from fpdf import FPDF
import qrcode
import os
import sys
import tempfile

def imprimer_ticket(mesures, fauteuil):
    """Génère un PDF et l'ouvre automatiquement (Windows/Linux)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Titre
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 180, 180)
    pdf.cell(0, 15, "CABINE FAUTEUILS", ln=True, align="C")
    pdf.ln(10)

    # Mesures
    pdf.set_font("Helvetica", "", 14)
    pdf.set_fill_color(20, 10, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "MESURES", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

    champs = [
        ("Taille", f"{mesures.get('taille', 0)} cm"),
        ("Poids", f"{mesures.get('poids', 0)} kg"),
        ("Hanches", f"{mesures.get('hanches', 0)} cm"),
        ("Épaules", f"{mesures.get('epaules', 0)} cm"),
        ("Profondeur d'assise", f"{mesures.get('profondeur_assise', 0)} cm"),
        ("Hauteur poplitée", f"{mesures.get('hauteur_poplitee', 0)} cm"),
        ("Hauteur dossier", f"{mesures.get('hauteur_dossier', 0)} cm"),
        ("IMC", f"{mesures.get('imc', 0)}"),
    ]
    for nom, val in champs:
        pdf.cell(80, 8, f"{nom} :", border=0)
        pdf.cell(0, 8, val, ln=True)

    pdf.ln(10)

    # Recommandation
    if fauteuil:
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 10, "FAUTEUIL RECOMMANDE", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, fauteuil["nom"], ln=True)
        pdf.cell(0, 8, f"Largeur assise : {fauteuil['largeur_assise_min']}-{fauteuil['largeur_assise_max']} cm", ln=True)
        pdf.cell(0, 8, f"Profondeur assise : {fauteuil['profondeur_assise_min']}-{fauteuil['profondeur_assise_max']} cm", ln=True)
        pdf.cell(0, 8, f"Hauteur dossier : {fauteuil['hauteur_dossier']} cm", ln=True)
        pdf.cell(0, 8, f"Charge max : {fauteuil['charge_max']} kg", ln=True)
        pdf.cell(0, 8, f"Hauteur assise réglable : {fauteuil['hauteur_assise_min']}-{fauteuil['hauteur_assise_max']} cm", ln=True)
        hauteur_rec = mesures.get('hauteur_poplitee', 0) - 2
        pdf.cell(0, 8, f"Hauteur d'assise recommandée : {hauteur_rec:.1f} cm", ln=True)
    else:
        pdf.cell(0, 8, "Aucun fauteuil adapté trouvé.", ln=True)

    # QR code – sauvegarde temporaire sur disque
    qr = qrcode.make("https://www.votresite.com/recommandation")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        qr.save(tmp.name)
        tmp_path = tmp.name

    pdf.image(tmp_path, x=150, y=250, w=40)
    os.unlink(tmp_path)  # nettoyage

    # Sauvegarde du PDF
    fichier = "ticket_recommandation.pdf"
    pdf.output(fichier)

    # Ouverture automatique
    if sys.platform == "win32":
        os.startfile(fichier)
    else:
        os.system(f"xdg-open '{fichier}'")