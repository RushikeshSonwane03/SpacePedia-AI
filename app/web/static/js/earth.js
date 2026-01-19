document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('earth-container');
    if (!container) return;

    // Configuration
    const textureUrl = container.getAttribute('data-texture-url');
    // Scene Setup
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 2.5;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Geometry & Material
    const geometry = new THREE.SphereGeometry(1, 64, 64);
    const textureLoader = new THREE.TextureLoader();

    // Default material 
    let material = new THREE.MeshPhongMaterial({
        color: 0x2233ff,
        emissive: 0x112244,
        specular: 0x111111,
        shininess: 10
    });

    if (textureUrl) {
        textureLoader.load(textureUrl, (texture) => {
            material = new THREE.MeshStandardMaterial({
                map: texture,
                roughness: 0.5,
                metalness: 0.1
            });
            earth.material = material;
        });
    }

    const earth = new THREE.Mesh(geometry, material);
    scene.add(earth);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.8); // Brighter
    directionalLight.position.set(5, 3, 5);
    scene.add(directionalLight);

    // Blue Atmosphere Glow (Point Light behind/side)
    const glowLight = new THREE.PointLight(0x0055ff, 2, 50);
    glowLight.position.set(-2, 1, 2);
    scene.add(glowLight);

    // --- STARS BACKGROUND ---
    function createStars() {
        const starGeo = new THREE.BufferGeometry();
        const starCount = 6000; // More stars
        const posArray = new Float32Array(starCount * 3);

        for (let i = 0; i < starCount * 3; i++) {
            // Random positions in a MUCH larger sphere to ensure full coverage
            posArray[i] = (Math.random() - 0.5) * 400;
        }

        starGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        const starMat = new THREE.PointsMaterial({
            size: 0.15, // Slightly larger
            color: 0xffffff,
            transparent: true,
            opacity: 0.9,
            sizeAttenuation: true
        });

        const stars = new THREE.Points(starGeo, starMat);
        scene.add(stars);
        return stars;
    }
    const starField = createStars();

    // --- SUN & GLOW ---
    function createGlowTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 256; // Higher res
        canvas.height = 256;
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);

        // Brighter, warmer gradient
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');      // White hot core
        gradient.addColorStop(0.1, 'rgba(255, 240, 200, 0.8)'); // Yellow core
        gradient.addColorStop(0.3, 'rgba(255, 200, 100, 0.4)'); // Orange halo
        gradient.addColorStop(0.6, 'rgba(255, 100, 50, 0.1)');  // Red fade
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 256, 256);
        return new THREE.CanvasTexture(canvas);
    }

    const sunMaterial = new THREE.SpriteMaterial({
        map: createGlowTexture(),
        color: 0xffffee,
        transparent: true,
        blending: THREE.AdditiveBlending
    });

    // Main Sun Glow
    const sunSprite = new THREE.Sprite(sunMaterial);
    sunSprite.scale.set(25, 25, 1); // Much Larger
    sunSprite.position.set(8, 5, -5); // Top Right, further back
    scene.add(sunSprite);

    // --- MOUSE INTERACTION (Parallax) ---
    let mouseX = 0;
    let mouseY = 0;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) - 0.5;
        mouseY = (event.clientY / window.innerHeight) - 0.5;
    });

    // Animation Loop
    let isAnimating = true;

    function animate() {
        if (isAnimating) {
            requestAnimationFrame(animate);
            earth.rotation.y += 0.0015;

            // Star rotation
            starField.rotation.y -= 0.0002;

            // Parallax
            const targetRotX = mouseY * 0.1;
            const targetRotY = mouseX * 0.1;

            scene.rotation.x += (targetRotX - scene.rotation.x) * 0.05;
            scene.rotation.y += (targetRotY - scene.rotation.y) * 0.05;

            renderer.render(scene, camera);
        }
    }

    animate();

    // Handle Resize
    window.addEventListener('resize', () => {
        const width = window.innerWidth;
        const height = window.innerHeight;

        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();

        // Responsive Scale
        if (width < 768) {
            earth.scale.set(0.8, 0.8, 0.8);
            sunSprite.scale.set(15, 15, 1);
        } else {
            earth.scale.set(1, 1, 1);
            sunSprite.scale.set(25, 25, 1);
        }
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            isAnimating = false;
        } else {
            isAnimating = true;
            animate();
        }
    });

    if (window.innerWidth < 768) {
        earth.scale.set(0.8, 0.8, 0.8);
        sunSprite.scale.set(15, 15, 1);
    }
});
