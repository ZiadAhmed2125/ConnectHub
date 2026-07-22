setTimeout(function () {
        const alerts = document.querySelectorAll(".flash-msg");
        for (alert of alerts)
        {
            if (alert) {
            alert.style.transition = "opacity 0.5s";
            alert.style.opacity = "0";

            setTimeout(() => alert.remove(), 500);
            }
        }
}, 3000);

document.querySelectorAll(".like-btn")

.forEach(button => {
    button.addEventListener("click", async function() {
        const postId = this.dataset.postId;

        const response = await fetch("/like", {
            headers: {
                "Content-Type": "application/json"
            },

            method: "POST",

            body: JSON.stringify({
                post_id: postId
            })

        });

        const data = await response.json();
        
        const posts_like = document.querySelectorAll(`.likes-${postId}`)

        for (const post of posts_like)
        {
            post.textContent = data.like_count;
        }

        const posts_heart = document.querySelectorAll(`.heart-${postId}`);

        for (const heart of posts_heart)
        {
            if (data.is_liked)
            {
                heart.classList.remove("bi-heart");
                heart.classList.add("bi-heart-fill");
                heart.classList.add("text-danger");
            }
            else
            {
                heart.classList.remove("bi-heart-fill");
                heart.classList.remove("text-danger");
                heart.classList.add("bi-heart");
            }
        }
    });
})