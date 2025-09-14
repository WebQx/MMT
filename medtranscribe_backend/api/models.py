from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# OpenEMR User Authentication Models
class OpenEMRUser(models.Model):
    """Maps to OpenEMR users table for authentication"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)  # OpenEMR uses PHP password_hash()
    email = models.EmailField(max_length=255, blank=True, null=True)
    fname = models.CharField(max_length=255, blank=True, null=True)
    lname = models.CharField(max_length=255, blank=True, null=True)
    mname = models.CharField(max_length=255, blank=True, null=True)
    federaltaxid = models.CharField(max_length=255, blank=True, null=True)
    federaldrugid = models.CharField(max_length=255, blank=True, null=True)
    upin = models.CharField(max_length=255, blank=True, null=True)
    facility_id = models.IntegerField(default=3)
    facility = models.CharField(max_length=255, blank=True, null=True)
    see_auth = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    npi = models.CharField(max_length=15, blank=True, null=True)
    title = models.CharField(max_length=30, blank=True, null=True)
    specialty = models.CharField(max_length=255, blank=True, null=True)
    billname = models.CharField(max_length=255, blank=True, null=True)
    valedictory = models.CharField(max_length=50, blank=True, null=True)
    assistant = models.CharField(max_length=255, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=60, blank=True, null=True)
    streetb = models.CharField(max_length=60, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    state = models.CharField(max_length=30, blank=True, null=True)
    zip = models.CharField(max_length=20, blank=True, null=True)
    street2 = models.CharField(max_length=60, blank=True, null=True)
    streetb2 = models.CharField(max_length=60, blank=True, null=True)
    city2 = models.CharField(max_length=30, blank=True, null=True)
    state2 = models.CharField(max_length=30, blank=True, null=True)
    zip2 = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=30, blank=True, null=True)
    phonew1 = models.CharField(max_length=30, blank=True, null=True)
    phonecell = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    cal_ui = models.CharField(max_length=50, default='1')
    taxonomy = models.CharField(max_length=30, default='207Q00000X')
    ssi_relayhealth = models.CharField(max_length=64, blank=True, null=True)
    calendar = models.BooleanField(default=True)
    abook_type = models.CharField(max_length=31, default='')
    pwd_expiration_date = models.DateField(default='0000-00-00')
    pwd_history1 = models.CharField(max_length=255, blank=True, null=True)
    pwd_history2 = models.CharField(max_length=255, blank=True, null=True)
    default_warehouse = models.CharField(max_length=31, blank=True, null=True)
    irnpool = models.CharField(max_length=31, blank=True, null=True)
    state_license_number = models.CharField(max_length=25, blank=True, null=True)
    newcrop_user_role = models.CharField(max_length=30, blank=True, null=True)
    cpoe = models.BooleanField(default=False)
    physician_type = models.CharField(max_length=50, blank=True, null=True)
    main_menu_role = models.CharField(max_length=50, default='')
    patient_menu_role = models.CharField(max_length=50, default='')
    weno_prov_id = models.CharField(max_length=10, blank=True, null=True)
    erx_username = models.CharField(max_length=50, blank=True, null=True)
    erx_password = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False  # This is an existing OpenEMR table
        db_table = 'users'

class OpenEMRSession(models.Model):
    """Maps to OpenEMR sessions table for PHP session management"""
    session_id = models.CharField(max_length=128, primary_key=True)
    session_data = models.TextField()
    last_updated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        managed = False  # This is an existing OpenEMR table  
        db_table = 'sessions'

# Patient Models
class Patient(models.Model):
    """Maps to OpenEMR patient_data table"""
    pid = models.AutoField(primary_key=True)
    title = models.CharField(max_length=4, default='')
    language = models.CharField(max_length=30, default='')
    financial = models.CharField(max_length=30, default='')
    fname = models.CharField(max_length=255, default='')
    lname = models.CharField(max_length=255, default='')
    mname = models.CharField(max_length=255, default='')
    DOB = models.DateField(null=True, blank=True)
    street = models.CharField(max_length=255, default='')
    postal_code = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=30, default='')
    state = models.CharField(max_length=30, default='')
    country_code = models.CharField(max_length=10, default='')
    drivers_license = models.CharField(max_length=255, default='')
    ss = models.CharField(max_length=255, default='')
    occupation = models.CharField(max_length=255, blank=True, null=True)
    phone_home = models.CharField(max_length=255, default='')
    phone_biz = models.CharField(max_length=255, default='')
    phone_contact = models.CharField(max_length=255, default='')
    phone_cell = models.CharField(max_length=255, default='')
    pharmacy_id = models.IntegerField(default=0)
    status = models.CharField(max_length=255, default='')
    contact_relationship = models.CharField(max_length=30, default='')
    date = models.DateTimeField(default=timezone.now)
    sex = models.CharField(max_length=30, default='')
    referrer = models.CharField(max_length=255, default='')
    referrerID = models.CharField(max_length=30, default='')
    providerID = models.IntegerField(null=True, blank=True)
    ref_providerID = models.IntegerField(null=True, blank=True)
    email = models.CharField(max_length=255, default='')
    email_direct = models.CharField(max_length=255, default='')
    ethnoracial = models.CharField(max_length=255, default='')
    race = models.CharField(max_length=255, default='')
    ethnicity = models.CharField(max_length=255, default='')
    religion = models.CharField(max_length=40, default='')
    interpretter = models.CharField(max_length=255, default='')
    migrantseasonal = models.CharField(max_length=255, default='')
    family_size = models.CharField(max_length=255, default='')
    monthly_income = models.CharField(max_length=255, default='')
    homeless = models.CharField(max_length=255, default='')
    financial_review = models.DateTimeField(default='0000-00-00 00:00:00')
    pubpid = models.CharField(max_length=255, unique=True, default='')
    pid = models.AutoField(primary_key=True)
    hipaa_mail = models.CharField(max_length=3, default='')
    hipaa_voice = models.CharField(max_length=3, default='')
    hipaa_notice = models.CharField(max_length=3, default='')
    hipaa_message = models.CharField(max_length=20, default='')
    hipaa_allowsms = models.CharField(max_length=3, default='NO')
    hipaa_allowemail = models.CharField(max_length=3, default='NO')
    squad = models.CharField(max_length=32, default='')
    fitness = models.IntegerField(default=0)
    referral_source = models.CharField(max_length=30, default='')
    usertext1 = models.CharField(max_length=255, default='')
    usertext2 = models.CharField(max_length=255, default='')
    usertext3 = models.CharField(max_length=255, default='')
    usertext4 = models.CharField(max_length=255, default='')
    usertext5 = models.CharField(max_length=255, default='')
    usertext6 = models.CharField(max_length=255, default='')
    usertext7 = models.CharField(max_length=255, default='')
    usertext8 = models.CharField(max_length=255, default='')
    userlist1 = models.CharField(max_length=255, default='')
    userlist2 = models.CharField(max_length=255, default='')
    userlist3 = models.CharField(max_length=255, default='')
    userlist4 = models.CharField(max_length=255, default='')
    userlist5 = models.CharField(max_length=255, default='')
    userlist6 = models.CharField(max_length=255, default='')
    userlist7 = models.CharField(max_length=255, default='')
    pricelevel = models.CharField(max_length=255, default='standard')
    regdate = models.DateField(null=True, blank=True)
    contrastart = models.DateField(null=True, blank=True)
    completed_ad = models.CharField(max_length=3, default='NO')
    ad_reviewed = models.DateField(null=True, blank=True)
    vfc = models.CharField(max_length=255, default='')
    mothersname = models.CharField(max_length=255, default='')
    guardiansname = models.CharField(max_length=255, default='')
    allow_imm_reg_use = models.CharField(max_length=255, default='')
    allow_imm_info_share = models.CharField(max_length=255, default='')
    allow_health_info_ex = models.CharField(max_length=255, default='')
    allow_patient_portal = models.CharField(max_length=31, default='')
    deceased_date = models.DateTimeField(null=True, blank=True)
    deceased_reason = models.CharField(max_length=255, default='')
    soap_import_status = models.SmallIntegerField(null=True, blank=True)
    cmsportal_login = models.CharField(max_length=60, default='')
    care_team = models.IntegerField(null=True, blank=True)
    county = models.CharField(max_length=40, default='')
    industry = models.CharField(max_length=255, blank=True, null=True)
    imm_reg_status = models.CharField(max_length=255, default='')
    imm_reg_stat_effdate = models.DateField(null=True, blank=True)
    publicity_code = models.CharField(max_length=255, default='')
    publ_code_eff_date = models.DateField(null=True, blank=True)
    protect_indicator = models.CharField(max_length=255, default='')
    prot_indi_effdate = models.DateField(null=True, blank=True)
    
    class Meta:
        managed = False  # This is an existing OpenEMR table
        db_table = 'patient_data'

# Encounter Models 
class Encounter(models.Model):
    """Maps to OpenEMR form_encounter table"""
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=255, default='')
    facility = models.CharField(max_length=255, default='')
    facility_id = models.IntegerField(default=0)
    pid = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='pid')
    encounter = models.BigIntegerField(default=0)
    onset_date = models.DateTimeField(null=True, blank=True)
    sensitivity = models.CharField(max_length=30, default='normal')
    billing_note = models.TextField(blank=True, null=True)
    pc_catid = models.IntegerField(default=5)
    last_level_billed = models.IntegerField(default=0)
    last_level_closed = models.IntegerField(default=0)
    last_stmt_date = models.DateField(null=True, blank=True)
    stmt_count = models.IntegerField(default=0)
    provider_id = models.ForeignKey(OpenEMRUser, on_delete=models.SET_NULL, null=True, blank=True, db_column='provider_id')
    supervisor_id = models.IntegerField(default=0)
    invoice_refno = models.CharField(max_length=31, default='')
    referral_source = models.CharField(max_length=31, default='')
    billing_facility = models.IntegerField(default=3)
    external_id = models.CharField(max_length=20, default='')
    pos_code = models.SmallIntegerField(default=0)
    class_code = models.CharField(max_length=20, default='AMB')
    
    class Meta:
        managed = False  # This is an existing OpenEMR table
        db_table = 'form_encounter'

# Medical Transcription Models (Custom tables for MMT)
class Transcription(models.Model):
    """Custom table for storing medical transcriptions"""
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, null=True, blank=True)
    provider = models.ForeignKey(OpenEMRUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transcription metadata
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Transcription content
    transcription_text = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)
    language_detected = models.CharField(max_length=10, default='en')
    
    # Processing status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Integration with OpenEMR
    openemr_note_id = models.IntegerField(null=True, blank=True)  # Reference to OpenEMR notes
    integrated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mmt_transcriptions'
        ordering = ['-created_at']

class TranscriptionSegment(models.Model):
    """Store individual segments/sentences of transcription for editing"""
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='segments')
    segment_number = models.IntegerField()
    start_time = models.FloatField(null=True, blank=True)  # seconds from start
    end_time = models.FloatField(null=True, blank=True)    # seconds from start
    text = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)
    edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(OpenEMRUser, on_delete=models.SET_NULL, null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mmt_transcription_segments'
        ordering = ['segment_number']
