/**
 * Mobile layout: drawer toggles and responsive controls.
 */

export function initMobileDrawer(): void {
  // Left sidebar drawer toggle for mobile
  const sidebarLeft = document.querySelector<HTMLElement>(".sidebar-left");
  const mainContent = document.querySelector<HTMLElement>(".content");

  if (!sidebarLeft) return;

  // Create hamburger button if it doesn't exist
  let menuBtn = document.getElementById("mobile-menu-btn");
  if (!menuBtn) {
    menuBtn = document.createElement("button");
    menuBtn.id = "mobile-menu-btn";
    menuBtn.className = "mobile-menu-btn";
    menuBtn.setAttribute("aria-label", "Toggle navigation");
    menuBtn.innerHTML = "&#9776;";
    const topbar = document.querySelector(".top-bar");
    if (topbar) {
      topbar.prepend(menuBtn);
    } else if (mainContent) {
      mainContent.prepend(menuBtn);
    }
  }

  menuBtn.addEventListener("click", () => {
    sidebarLeft.classList.toggle("open");
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", (e) => {
    if (window.innerWidth > 768) return;
    const target = e.target as HTMLElement;
    if (!sidebarLeft.classList.contains("open")) return;
    if (!sidebarLeft.contains(target) && target !== menuBtn) {
      sidebarLeft.classList.remove("open");
    }
  });

  // Right sidebar: bottom tabs on mobile
  const sidebarRight = document.querySelector<HTMLElement>(".sidebar-right");
  if (sidebarRight && window.innerWidth <= 768) {
    sidebarRight.classList.add("mobile-tabs");
  }

  // Handle window resize
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      sidebarLeft.classList.remove("open");
      sidebarRight?.classList.remove("mobile-tabs");
    } else {
      sidebarRight?.classList.add("mobile-tabs");
    }
  });
}
