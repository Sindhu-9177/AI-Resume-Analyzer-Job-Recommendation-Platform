async function analyzeResume() {

    const fileInput = document.getElementById("resumeFile");
    const loading = document.getElementById("loading");
    const errorBox = document.getElementById("errorBox");

    const file = fileInput.files[0];

    // Reset UI
    document.getElementById("atsScore").innerText = "--";
    document.getElementById("skillsContainer").innerHTML = "";
    document.getElementById("jobsContainer").innerHTML = "";

    errorBox.classList.add("d-none");

    if (!file) {
        errorBox.innerText = "Please select a resume file";
        errorBox.classList.remove("d-none");
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);

    loading.classList.remove("d-none");

    try {

        const response = await fetch("/analyze", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        loading.classList.add("d-none");

        if (data.error) {
            errorBox.innerText = data.error;
            errorBox.classList.remove("d-none");
            return;
        }

        // =====================
        // ATS SCORE
        // =====================
        document.getElementById("atsScore").innerText = data.ats_score || 0;

        // =====================
        // SKILLS
        // =====================
        let skillsHTML = "";

        if (data.skills && data.skills.length > 0) {
            data.skills.forEach(skill => {
                skillsHTML += `<span class="skill-badge">${skill}</span>`;
            });
        } else {
            skillsHTML = "<p class='text-muted'>No skills detected</p>";
        }

        document.getElementById("skillsContainer").innerHTML = skillsHTML;

        // =====================
        // JOBS
        // =====================
        let jobsHTML = "";

        if (data.jobs && data.jobs.length > 0) {

            data.jobs.forEach(job => {

                let jobLink = job.url || job.redirect_url || "#";

                jobsHTML += `
                <div class="col-md-4 mb-3">
                    <div class="card job-card p-3 h-100">

                        <h5 class="job-title">${job.title || "No Title"}</h5>

                        <p class="job-company">🏢 ${job.company || "Unknown"}</p>

                        <p class="job-location">📍 ${job.location || "N/A"}</p>

                        <button class="btn btn-primary w-100 mt-2"
                            onclick="openJob('${jobLink}')">
                            View Job
                        </button>

                    </div>
                </div>
                `;
            });

        } else {
            jobsHTML = "<p class='text-muted'>No jobs found</p>";
        }

        document.getElementById("jobsContainer").innerHTML = jobsHTML;

    }
    catch (error) {

        loading.classList.add("d-none");

        errorBox.innerText = "Something went wrong. Try again.";
        errorBox.classList.remove("d-none");

        console.error(error);
    }
}


// =====================
// OPEN JOB SAFELY
// =====================
function openJob(url) {

    if (!url || url === "#") {
        alert("Job link not available");
        return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
}