INSERT INTO departments(name,description) VALUES
('Cardiology','Heart and cardiovascular care'),('Dermatology','Skin, hair, and nail care'),('General Medicine','Primary adult medical care') ON CONFLICT(name) DO NOTHING;
INSERT INTO doctors(department_id,name) SELECT id,'Dr. Ananya Rao' FROM departments WHERE name='Cardiology' AND NOT EXISTS(SELECT 1 FROM doctors WHERE name='Dr. Ananya Rao');
INSERT INTO doctors(department_id,name) SELECT id,'Dr. Vikram Shah' FROM departments WHERE name='Dermatology' AND NOT EXISTS(SELECT 1 FROM doctors WHERE name='Dr. Vikram Shah');
INSERT INTO doctors(department_id,name) SELECT id,'Dr. Meera Iyer' FROM departments WHERE name='General Medicine' AND NOT EXISTS(SELECT 1 FROM doctors WHERE name='Dr. Meera Iyer');
INSERT INTO slots(doctor_id,starts_at,duration_minutes) SELECT d.id,date_trunc('day',now())+i*interval '1 day'+time '10:00',30 FROM doctors d CROSS JOIN generate_series(1,14) i WHERE NOT EXISTS(SELECT 1 FROM slots) ;
INSERT INTO knowledge_documents(title,content,source_url,authority,metadata) VALUES
('Hospital hours','Outpatient departments are open Monday through Saturday from 8:00 AM to 6:00 PM. The emergency department is open 24 hours every day.','hospital://policy/hours',3,'{"category":"hours","approved":true}'),
('Appointment policy','Patients should arrive 15 minutes before an appointment. Bring a photo ID, prior reports, and insurance information if applicable. Cancellations should be made at least 4 hours before the visit.','hospital://policy/appointments',3,'{"category":"appointments","approved":true}'),
('Emergency disclaimer','The assistant does not diagnose emergencies. For chest pain, severe breathing difficulty, unconsciousness, stroke signs, or severe bleeding, call the local emergency number immediately.','hospital://policy/emergency',5,'{"category":"safety","approved":true}'),
('Cardiology department','Cardiology evaluates heart and circulation concerns. Administrative staff can schedule a consultation, but only a clinician can provide medical advice or diagnosis.','hospital://department/cardiology',2,'{"category":"department","approved":true}'),
('Dermatology department','Dermatology provides consultations for skin, hair, and nail concerns. The assistant can help schedule a visit but cannot diagnose a condition.','hospital://department/dermatology',2,'{"category":"department","approved":true}')
ON CONFLICT DO NOTHING;
