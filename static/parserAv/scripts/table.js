const addCarForm = document.getElementById('add-ads'),
      closeForm = document.getElementById('add-ads__form__close-btn'),
      add_ads = document.getElementById('add__adds'),
      loader = document.getElementById('loader'),
      add_car_btn = document.getElementById('add-ads__form__btn')
      table_cell_list = document.getElementsByTagName('td')

closeForm.addEventListener('click', () =>{
  addCarForm.style.display='none'
  document.getElementById('wrapper').style.filter='none'
})

add_ads.addEventListener('click', () =>{
  addCarForm.style.display='flex'
  document.getElementById('wrapper').style.filter='blur(20px)'
})

add_car_btn.addEventListener('click', () => {
  addCarForm.style.display='none'
  loader.style.display = 'flex'
})

for (let i=0; i < table_cell_list.length; i++) {
  if (table_cell_list[i].className != 'table__data__row__link' && table_cell_list[i].parentNode.getAttribute('page_link') != null) {
    table_cell_list[i].addEventListener('click', () => {
      location.href=(`http://127.0.0.1:8000${table_cell_list[i].parentNode.getAttribute('page_link')}`)
    })
  }
}
