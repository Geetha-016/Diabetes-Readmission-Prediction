CREATE DATABASE hospital_readmission_db;
USE hospital_readmission_db;

CREATE TABLE diabetes_readmission (
    race VARCHAR(50),
    gender VARCHAR(30),
    age VARCHAR(20),
    admission_type_id INT,
    discharge_disposition_id INT,
    admission_source_id INT,
    time_in_hospital INT,
    payer_code VARCHAR(50),
    medical_specialty VARCHAR(100),
    num_lab_procedures INT,
    num_procedures INT,
    num_medications INT,
    number_outpatient INT,
    number_emergency INT,
    number_inpatient INT,
    diag_1 VARCHAR(20),
    diag_2 VARCHAR(20),
    diag_3 VARCHAR(20),
    number_diagnoses INT,
    metformin VARCHAR(20),
    repaglinide VARCHAR(20),
    nateglinide VARCHAR(20),
    chlorpropamide VARCHAR(20),
    glimepiride VARCHAR(20),
    acetohexamide VARCHAR(20),
    glipizide VARCHAR(20),
    glyburide VARCHAR(20),
    tolbutamide VARCHAR(20),
    pioglitazone VARCHAR(20),
    rosiglitazone VARCHAR(20),
    acarbose VARCHAR(20),
    miglitol VARCHAR(20),
    troglitazone VARCHAR(20),
    tolazamide VARCHAR(20),
    examide VARCHAR(20),
    citoglipton VARCHAR(20),
    insulin VARCHAR(20),
    `glyburide-metformin` VARCHAR(20),
    `glipizide-metformin` VARCHAR(20),
    `glimepiride-pioglitazone` VARCHAR(20),
    `metformin-rosiglitazone` VARCHAR(20),
    `metformin-pioglitazone` VARCHAR(20),
    `change` VARCHAR(20),
    diabetesMed VARCHAR(20),
    readmitted INT
);

DESCRIBE diabetes_readmission;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/diabetic_data_1.csv'
INTO TABLE diabetes_readmission
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;

SELECT * FROM diabetes_readmission;

-- Q1. Overall readmission rate
SELECT ROUND(AVG(readmitted) * 100,2) as readmission_rate
FROM diabetes_readmission;

-- Q2. Readmission rate by age group 
SELECT age, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY age
ORDER BY readmission_rate DESC;

-- Q3. Readmission rate by gender
SELECT gender, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY gender
ORDER BY readmission_rate DESC;

-- Q4. Readmission rate by race
SELECT race, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY race
ORDER BY readmission_rate DESC;

-- Q5. Which Admission Type has Highest Readmission ? 
SELECT admission_type_id, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY admission_type_id
ORDER BY readmission_rate;

-- Q6. Average Hospital Stay for Readmitted vs Non-Readmitted Patients
SELECT readmitted, ROUND(AVG(time_in_hospital)*100,2) as avg_hospital_stay
FROM diabetes_readmission
GROUP BY readmitted;

-- Q7. Top 10 Medical Specialties with Highest Readmission Rate 
SELECT medical_specialty, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY medical_specialty
HAVING COUNT(*) > 100
ORDER BY readmission_rate DESC
LIMIT 10;

-- Q8. Readmission rate by Number of Diagnoses
SELECT number_diagnoses, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY number_diagnoses
ORDER BY readmission_rate DESC;

-- Q9. Average number of Medications by Readmission Status
SELECT readmitted, ROUND(AVG(num_medications)*100,2) as avg_medications
FROM diabetes_readmission
GROUP BY readmitted
ORDER BY avg_medications DESC;

-- Q10. Average Lab Procedures by Readmission Status
SELECT readmitted, ROUND(AVG(num_lab_procedures)*100,2) as avg_lab_procedures
FROM diabetes_readmission
GROUP BY readmitted
ORDER BY avg_lab_procedures DESC;

-- Q11. Which Age group spends longest time in hospital ? 
SELECT age, ROUND(AVG(time_in_hospital)*100,2) as avg_stay 
FROM diabetes_readmission
GROUP BY age
ORDER BY avg_stay DESC;

-- Q12. Patients with Highest Prior Inpatient Visits
SELECT number_inpatient, COUNT(*) as patients, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY number_inpatient
HAVING COUNT(*) >= 100
ORDER BY number_inpatient;

-- Q13. Impact of insulin on Readmission
SELECT insulin, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY insulin
ORDER BY readmission_rate DESC;

-- Q14. Impact of Diabetes Medication on Readmission
SELECT diabetesMed, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY diabetesMed
ORDER BY readmission_rate DESC;

-- Q15. Readmission Rate by Change in Medication 
SELECT `change`, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY `change`
ORDER BY readmission_rate DESC;

-- Q16. Rank Medical Specialties by Readmission Rate 
SELECT medical_specialty, ROUND(AVG(readmitted)*100,2) as readmission_rate, DENSE_RANK()OVER(ORDER BY AVG(readmitted) DESC) as specialty_rank 
FROM diabetes_readmission
GROUP BY medical_specialty;

-- Q17. Top 5 Highest Risk Age Groups 
SELECT age, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY age
ORDER BY readmission_rate DESC
LIMIT 5;

-- Q18. Readmission Rate by Age and Gender Combination
SELECT age, gender, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY age, gender
ORDER BY readmission_rate DESC;

-- Q19. Which Combination of Admission Type and Source has Highest Readmission ? 
SELECT admission_type_id, admission_source_id, ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY admission_type_id, admission_source_id
ORDER BY readmission_rate DESC
LIMIT 1;

-- Q20. Create Patient Risk Categories
SELECT CASE WHEN number_inpatient >=5 THEN 'High Risk' 
WHEN number_inpatient >=2 THEN 'Medium Risk'
ELSE 'Low Risk'
END as risk_category, 
ROUND(AVG(readmitted)*100,2) as readmission_rate
FROM diabetes_readmission
GROUP BY risk_category
ORDER BY readmission_rate DESC;