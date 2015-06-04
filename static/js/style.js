var images = ['image1.jpg', 'image2.jpg', 'image3.jpg', 'image4.jpg'];
$('body').css({'background-image': 'url("/static/img/bg/' + images[Math.floor(Math.random() * images.length)] + '")'});