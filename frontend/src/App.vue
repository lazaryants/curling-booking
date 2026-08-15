<template>
  <div id="app">
    <Navbar />
    <router-view />
    <AppDialog />
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'
import AppDialog from './components/AppDialog.vue'

export default {
  components: {
    Navbar,
    AppDialog
  }
}
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
