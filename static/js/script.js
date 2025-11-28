// Ensure video plays on mobile devices
document.addEventListener('DOMContentLoaded', function() {
    const video = document.querySelector('.hero-video');
    
    if (video) {
        video.play().catch(function(error) {
            console.log('Video autoplay failed:', error);
        });
    }
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    hamburger.addEventListener('click', function() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close mobile menu when clicking on a link
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
});

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Contact Form Submission with Web3Forms
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    const formStatus = document.getElementById('formStatus');

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitButton = form.querySelector('.submit-button');
            const formData = new FormData(form);
            
            // Disable button and show loading state
            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';
            formStatus.textContent = '';
            formStatus.className = 'form-status';

            try {
                const response = await fetch('https://api.web3forms.com/submit', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    formStatus.textContent = 'Message sent successfully! We\'ll get back to you soon.';
                    formStatus.classList.add('success');
                    form.reset();
                } else {
                    formStatus.textContent = 'Something went wrong. Please try again.';
                    formStatus.classList.add('error');
                }
            } catch (error) {
                formStatus.textContent = 'Network error. Please check your connection and try again.';
                formStatus.classList.add('error');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Send Message';
            }
        });
    }
});
