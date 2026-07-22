// Automatically fade out and remove flash messages after 3 seconds
setTimeout(function() {
    // Select all flash messages
    const alerts = document.querySelectorAll(".flash-msg");

    // Fade out each flash message
    for (alert of alerts) {
        if (alert) {
            alert.style.transition = "opacity 0.5s";
            alert.style.opacity = "0";

            // Remove the element after the fade animation completes
            setTimeout(() => alert.remove(), 500);
        }
    }
}, 3000);

// Add a click event listener to every like button
document.querySelectorAll(".like-btn")

    .forEach(button => {
        button.addEventListener("click", async function() {
            // Get the ID of the post associated with the clicked button
            const postId = this.dataset.postId;

            // Send a request to like/unlike the post
            const response = await fetch("/like", {
                headers: {
                    "Content-Type": "application/json"
                },

                method: "POST",

                body: JSON.stringify({
                    post_id: postId
                })

            });

            // Parse the JSON response from the server
            const data = await response.json();

            // Update the like count on all instances of the post
            const posts_like = document.querySelectorAll(`.likes-${postId}`)

            for (const post of posts_like) {
                post.textContent = data.like_count;
            }

            // Update the heart icon on all instances of the post
            const posts_heart = document.querySelectorAll(`.heart-${postId}`);

            for (const heart of posts_heart) {
                if (data.is_liked) {
                    // Switch to a filled red heart if the post is liked
                    heart.classList.remove("bi-heart");
                    heart.classList.add("bi-heart-fill");
                    heart.classList.add("text-danger");
                } else {
                    // Switch back to an empty heart if the post is unliked
                    heart.classList.remove("bi-heart-fill");
                    heart.classList.remove("text-danger");
                    heart.classList.add("bi-heart");
                }
            }
        });
    })